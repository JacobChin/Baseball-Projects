
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
for path in [SRC, SCRIPTS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from create_swing_qc_viewer import build_payload, render_html  # noqa: E402
from analyze_initiation_relationships import calculate_swing_lengths  # noqa: E402
from obp_swing_time.pipeline import (  # noqa: E402
    PRIMARY_CONFIG,
    expected_paths,
    median_dt,
    read_csv,
    read_zipped_csv,
    smooth_positions,
    validate_paths,
)

DATA_ROOT = Path(r"E:\Baseball\Data\OBP")
OUT_DIR = PROJECT_ROOT / "outputs" / "attack_angle_zone"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures" / "attack_angle_zone"
VIEWER_DIR = PROJECT_ROOT / "outputs" / "qc_viewers_attack_angle_zone"
IDEAL_MIN_DEG = 5.0
IDEAL_MAX_DEG = 20.0
ATTACK_ZONE_MIN_SPEED_PCT = 0.30
ATTACK_ZONE_AFTER_CONTACT_S = 0.10
ATTACK_DIRECTION_WINDOW_END_DEG = 55.0
MARKER_AA_TIME_OFFSET_S = -0.0063
M_TO_IN = 39.3700787402


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    VIEWER_DIR.mkdir(parents=True, exist_ok=True)

    paths = expected_paths(DATA_ROOT)
    validate_paths(paths)

    model = pd.read_csv(PROJECT_ROOT / "outputs" / "model_dataset.csv")
    manifest = pd.read_csv(PROJECT_ROOT / "outputs" / "swing_manifest.csv")
    current_onsets = pd.read_csv(PROJECT_ROOT / "outputs" / "onset_metrics.csv")
    velocity20 = pd.read_csv(PROJECT_ROOT / "outputs" / "initiation_analysis" / "velocity20_primary_model" / "velocity20_primary_onset_rows.csv")
    metadata = read_csv(paths["metadata"])
    for df in [model, manifest, current_onsets, velocity20, metadata]:
        df["session_swing"] = df["session_swing"].astype(str)

    ready = model.loc[model["model_ready_primary"].fillna(False).astype(bool)].copy()
    selected = set(ready["session_swing"].astype(str))
    landmarks = read_zipped_csv(paths["landmarks"], selected)
    landmarks["session_swing"] = landmarks["session_swing"].astype(str)

    print("Calculating swing windows from barrel path inflection...")
    swing_lengths = calculate_swing_lengths(landmarks)
    swing_lengths["session_swing"] = swing_lengths["session_swing"].astype(str)

    base_cols = [
        "session_swing", "user", "session", "hitter_side", "highest_playing_level",
        "bat_speed_mph_max_x", "attack_angle_contact_x", "model_ready_primary",
    ]
    data = ready[[c for c in base_cols if c in ready.columns]].copy()
    data = data.merge(manifest[["session_swing", "contact_time", "force_climb_start_time", "lead_force_max_time", "fp_100_time"]], on="session_swing", how="left")
    data = data.merge(velocity20[[
        "session_swing",
        "pelvis_velocity20_onset_time", "pelvis_velocity20_to_contact_ms",
        "torso_velocity20_onset_time", "torso_velocity20_to_contact_ms",
        "lead_hand_velocity20_onset_time", "lead_hand_velocity20_to_contact_ms",
        "velocity20_composite_swing_time_ms", "velocity20_initiation_spread_ms",
    ]], on="session_swing", how="left")
    data = data.merge(swing_lengths, on="session_swing", how="left")

    rows = []
    for sid, group in landmarks.groupby("session_swing", sort=False):
        row = data.loc[data["session_swing"].eq(str(sid))]
        if row.empty:
            continue
        rows.append(compute_swing_attack_metrics(str(sid), group, row.iloc[0]))
    metrics = pd.DataFrame(rows)
    data = data.merge(metrics, on="session_swing", how="left")
    data.to_csv(OUT_DIR / "attack_angle_zone_metrics.csv", index=False)

    summaries = summarize_metrics(data)
    summaries.to_csv(OUT_DIR / "attack_angle_zone_distribution_summary.csv", index=False)
    contact_compare = contact_comparison(data)
    contact_compare.to_csv(OUT_DIR / "attack_angle_contact_comparison_summary.csv", index=False)

    hitter_summary = make_hitter_summary(data)
    hitter_summary.to_csv(OUT_DIR / "attack_angle_zone_hitter_summary.csv", index=False)

    plot_distributions(data)
    plot_contact_comparison(data)
    plot_top_hitters(hitter_summary)

    examples = choose_examples(data)
    examples.to_csv(OUT_DIR / "attack_angle_zone_viewer_examples.csv", index=False)
    write_attack_viewers(examples, landmarks, manifest, current_onsets, metadata, velocity20, paths)

    print("distribution_summary")
    print(summaries.round(3).to_string(index=False))
    print("contact_comparison")
    print(contact_compare.round(3).to_string(index=False))
    print("examples")
    cols = ["example_type", "session_swing", "attack_zone_time_ms", "attack_zone_pct_of_swing", "longest_attack_zone_ms", "attack_angle_contact_computed_deg", "attack_angle_contact_x"]
    print(examples[[c for c in cols if c in examples.columns]].round(2).to_string(index=False))
    print("metrics_csv", OUT_DIR / "attack_angle_zone_metrics.csv")
    print("summary_csv", OUT_DIR / "attack_angle_zone_distribution_summary.csv")
    print("hitter_summary_csv", OUT_DIR / "attack_angle_zone_hitter_summary.csv")
    print("viewer_index", VIEWER_DIR / "index.html")
    return 0


def interpolate_series_at_times(time: np.ndarray, values: np.ndarray, query_times: np.ndarray) -> np.ndarray:
    valid = np.isfinite(time) & np.isfinite(values)
    if valid.sum() < 2:
        return np.full_like(query_times, np.nan, dtype=float)
    return np.interp(query_times, time[valid], values[valid], left=np.nan, right=np.nan)


def keep_zone_segment_nearest_contact(in_zone: np.ndarray, time: np.ndarray, contact: float) -> np.ndarray:
    filtered = np.zeros_like(in_zone, dtype=bool)
    valid = np.asarray(in_zone, dtype=bool) & np.isfinite(time)
    if not valid.any() or not np.isfinite(contact):
        return filtered
    idx = np.where(valid)[0]
    segments = []
    start = int(idx[0])
    prev = int(idx[0])
    for cur in idx[1:]:
        cur = int(cur)
        if cur == prev + 1:
            prev = cur
        else:
            segments.append((start, prev))
            start = prev = cur
    segments.append((start, prev))
    best = min(segments, key=lambda seg: np.nanmin(np.abs(time[seg[0]:seg[1] + 1] - contact)))
    filtered[best[0]:best[1] + 1] = valid[best[0]:best[1] + 1]
    return filtered


def latest_upward_crossing_time(time: np.ndarray, values: np.ndarray, threshold: float, start_time: float) -> float:
    if not np.isfinite(start_time):
        return np.nan
    valid = np.isfinite(time) & np.isfinite(values)
    if valid.sum() < 2:
        return np.nan
    t = time[valid]
    v = values[valid]
    order = np.argsort(t)
    t = t[order]
    v = v[order]
    if start_time < t[0] or start_time > t[-1]:
        return np.nan
    start_value = float(np.interp(start_time, t, v))
    if not np.isfinite(start_value):
        return np.nan
    keep = t > start_time
    tw = np.concatenate(([start_time], t[keep]))
    vw = np.concatenate(([start_value], v[keep]))
    crossings: list[float] = []
    for i in range(1, len(tw)):
        prev = vw[i - 1]
        cur = vw[i]
        if not np.isfinite(prev) or not np.isfinite(cur):
            continue
        if prev < threshold <= cur:
            if cur == prev:
                crossings.append(float(tw[i]))
            else:
                frac = (threshold - prev) / (cur - prev)
                crossings.append(float(tw[i - 1] + frac * (tw[i] - tw[i - 1])))
    return crossings[-1] if crossings else np.nan


def path_length_between_times(time: np.ndarray, xyz: np.ndarray, start_time: float, end_time: float) -> float:
    if not np.isfinite(start_time) or not np.isfinite(end_time) or end_time <= start_time:
        return np.nan
    valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
    if valid.sum() < 2:
        return np.nan
    t = time[valid]
    p = xyz[valid]
    order = np.argsort(t)
    t = t[order]
    p = p[order]
    if start_time < t[0] or end_time > t[-1]:
        return np.nan
    keep = (t > start_time) & (t < end_time)
    times = np.concatenate(([start_time], t[keep], [end_time]))
    pts = np.column_stack([np.interp(times, t, p[:, axis]) for axis in range(3)])
    diffs = np.diff(pts, axis=0)
    dist = np.linalg.norm(diffs, axis=1)
    return float(np.nansum(dist)) if np.isfinite(dist).any() else np.nan


def swing_path_tilt_deg(time: np.ndarray, xyz: np.ndarray, contact_time: float, window_s: float = 0.040) -> float:
    if not np.isfinite(contact_time):
        return np.nan
    valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
    mask = valid & (time >= contact_time - window_s) & (time <= contact_time)
    pts = xyz[mask]
    if pts.shape[0] < 4:
        return np.nan
    centered = pts - np.nanmean(pts, axis=0)
    if not np.isfinite(centered).all():
        return np.nan
    try:
        _, singular_values, vh = np.linalg.svd(centered, full_matrices=False)
    except np.linalg.LinAlgError:
        return np.nan
    if len(singular_values) < 3 or singular_values[1] <= 1e-9:
        return np.nan
    normal = vh[-1]
    norm = np.linalg.norm(normal)
    if not np.isfinite(norm) or norm <= 0:
        return np.nan
    normal = normal / norm
    vertical_component = min(1.0, max(0.0, abs(float(normal[2]))))
    return float(np.degrees(np.arccos(vertical_component)))


def compute_attack_series(group: pd.DataFrame) -> dict[str, np.ndarray | float]:
    g = group.sort_values("time").copy()
    needed = ["time", "sweet_spot_x", "sweet_spot_y", "sweet_spot_z"]
    if not set(needed).issubset(g.columns):
        return {"ok": False}
    for col in needed:
        g[col] = pd.to_numeric(g[col], errors="coerce")
    if "centerofmass_x" in g.columns:
        g["centerofmass_x"] = pd.to_numeric(g["centerofmass_x"], errors="coerce")
    else:
        g["centerofmass_x"] = np.nan
    if "centerofmass_y" in g.columns:
        g["centerofmass_y"] = pd.to_numeric(g["centerofmass_y"], errors="coerce")
    else:
        g["centerofmass_y"] = np.nan
    t = g["time"].to_numpy(float)
    xyz = g[["sweet_spot_x", "sweet_spot_y", "sweet_spot_z"]].to_numpy(float)
    com_x = g["centerofmass_x"].to_numpy(float)
    com_y = g["centerofmass_y"].to_numpy(float)
    valid = np.isfinite(t) & np.isfinite(xyz).all(axis=1)
    if valid.sum() < 12:
        return {"ok": False}
    dt = median_dt(t[valid])
    if not np.isfinite(dt) or dt <= 0:
        return {"ok": False}
    smoothed = xyz.copy()
    smoothed[valid] = smooth_positions(xyz[valid], dt, PRIMARY_CONFIG.smooth_ms)
    vx = np.gradient(smoothed[:, 0], t)
    vy = np.gradient(smoothed[:, 1], t)
    vz = np.gradient(smoothed[:, 2], t)

    # Primary attack angle for this project: side-view sweet-spot travel relative to ground.
    # 0 deg means the sweet spot is moving parallel to the ground in x/z; positive is upward.
    horizontal_x = np.abs(vx)
    attack_side_xz = np.degrees(np.arctan2(vz, horizontal_x))

    # Keep the older 3D ground-plane version for comparison only.
    horizontal_3d = np.sqrt(vx * vx + vy * vy)
    attack_3d_compare = np.degrees(np.arctan2(vz, horizontal_3d))
    speed = np.sqrt(vx * vx + vy * vy + vz * vz)

    # Avoid labeling frames where side-view horizontal motion is too small to define a stable angle.
    valid_horizontal = valid & (horizontal_x >= 0.50) & (speed >= 1.00)
    attack_side_xz[~valid_horizontal] = np.nan
    attack_3d_compare[~valid] = np.nan
    speed[~valid] = np.nan
    return {
        "ok": True,
        "time": t,
        "xyz": smoothed,
        "com_x": com_x,
        "com_y": com_y,
        "attack_3d": attack_side_xz,
        "attack_xz": attack_side_xz,
        "attack_3d_compare": attack_3d_compare,
        "speed": speed,
        "vx": vx,
        "vy": vy,
        "vz": vz,
    }

def compute_swing_attack_metrics(sid: str, group: pd.DataFrame, base_row: pd.Series) -> dict[str, object]:
    out: dict[str, object] = {"session_swing": sid}
    series = compute_attack_series(group)
    if not series.get("ok"):
        out["attack_angle_qc"] = "bad_attack_series"
        return out
    t = np.asarray(series["time"], dtype=float)
    xyz = np.asarray(series["xyz"], dtype=float)
    raw_aa = np.asarray(series["attack_3d"], dtype=float)
    raw_aa_xz = np.asarray(series["attack_xz"], dtype=float)
    raw_speed = np.asarray(series["speed"], dtype=float)
    query_t = t + MARKER_AA_TIME_OFFSET_S
    aa = interpolate_series_at_times(t, raw_aa, query_t)
    aa_xz = interpolate_series_at_times(t, raw_aa_xz, query_t)
    speed = interpolate_series_at_times(t, raw_speed, query_t)
    vx = interpolate_series_at_times(t, np.asarray(series.get("vx", np.full_like(t, np.nan)), dtype=float), query_t)
    vy = interpolate_series_at_times(t, np.asarray(series.get("vy", np.full_like(t, np.nan)), dtype=float), query_t)
    attack_direction_raw = np.degrees(np.arctan2(vy, np.abs(vx)))
    hitter_side = str(base_row.get("hitter_side", "")).upper()
    direction_sign = -1.0 if hitter_side == "L" else 1.0
    attack_direction_pull = attack_direction_raw * direction_sign
    com_x = np.asarray(series.get("com_x", np.full_like(t, np.nan)), dtype=float)
    com_y = np.asarray(series.get("com_y", np.full_like(t, np.nan)), dtype=float)
    contact = pd.to_numeric(pd.Series([base_row.get("contact_time")]), errors="coerce").iloc[0]
    if not np.isfinite(contact):
        out["attack_angle_qc"] = "missing_contact"
        return out
    lead_hand_start = pd.to_numeric(pd.Series([base_row.get("lead_hand_velocity20_onset_time")]), errors="coerce").iloc[0]
    if np.isfinite(lead_hand_start):
        start = float(lead_hand_start)
        start_source = "lead_hand_velocity20_onset"
    else:
        start = float(contact - 0.20)
        start_source = "fallback_200ms_before_contact"

    ad55_crossing = latest_upward_crossing_time(t, attack_direction_pull, ATTACK_DIRECTION_WINDOW_END_DEG, start)
    if np.isfinite(ad55_crossing) and ad55_crossing > start:
        end = float(ad55_crossing)
        end_source = "latest_upward_crossing_55deg_pull_attack_direction"
    else:
        end = float(contact + ATTACK_ZONE_AFTER_CONTACT_S)
        end_source = "fallback_contact_plus_100ms_no_ad55_crossing"
    out["attack_angle_window_source"] = f"{start_source}_to_{end_source}"
    out["attack_angle_window_start_source"] = start_source
    out["attack_angle_window_end_source"] = end_source
    out["attack_angle_window_end_attack_direction_deg"] = ATTACK_DIRECTION_WINDOW_END_DEG
    out["attack_angle_window_start_ms_before_contact"] = float((contact - start) * 1000.0)
    out["attack_angle_window_end_ms_after_contact"] = float((end - contact) * 1000.0)
    out["attack_angle_window_end_ms_before_contact"] = float((contact - end) * 1000.0)
    out["attack_angle_marker_time_offset_ms"] = MARKER_AA_TIME_OFFSET_S * 1000.0
    mask = (t >= start) & (t <= end) & np.isfinite(aa)
    if mask.sum() < 4:
        out["attack_angle_qc"] = "too_few_window_frames"
        return out
    max_window_speed = float(np.nanmax(speed[mask & np.isfinite(speed)])) if (mask & np.isfinite(speed)).any() else np.nan
    speed_gate = max_window_speed * ATTACK_ZONE_MIN_SPEED_PCT if np.isfinite(max_window_speed) else np.nan
    speed_ok = np.isfinite(speed) & np.isfinite(speed_gate) & (speed >= speed_gate)
    direction_ok = np.isfinite(attack_direction_pull)
    raw_in_zone = mask & speed_ok & direction_ok & (aa >= IDEAL_MIN_DEG) & (aa <= IDEAL_MAX_DEG)
    in_zone = keep_zone_segment_nearest_contact(raw_in_zone, t, contact)
    out["attack_angle_speed_gate_pct"] = ATTACK_ZONE_MIN_SPEED_PCT * 100.0
    out["attack_angle_speed_gate_mps"] = speed_gate
    out["attack_angle_max_window_speed_mps"] = max_window_speed
    contact_i = int(np.nanargmin(np.abs(t - contact)))
    out["attack_angle_contact_computed_deg"] = float(aa[contact_i]) if np.isfinite(aa[contact_i]) else np.nan
    out["attack_angle_contact_xz_deg"] = float(aa_xz[contact_i]) if np.isfinite(aa_xz[contact_i]) else np.nan
    obp = pd.to_numeric(pd.Series([base_row.get("attack_angle_contact_x")]), errors="coerce").iloc[0]
    out["attack_angle_contact_obp_deg"] = obp
    out["attack_angle_contact_diff_deg"] = float(aa[contact_i] - obp) if np.isfinite(aa[contact_i]) and np.isfinite(obp) else np.nan
    out["attack_angle_contact_speed_mps"] = float(speed[contact_i]) if np.isfinite(speed[contact_i]) else np.nan
    out["attack_angle_contact_bat_speed_mph"] = float(speed[contact_i] * 2.2369362920544) if np.isfinite(speed[contact_i]) else np.nan
    out["attack_angle_contact_speed_pct_max"] = float(speed[contact_i] / max_window_speed * 100.0) if np.isfinite(speed[contact_i]) and np.isfinite(max_window_speed) and max_window_speed > 0 else np.nan
    out["attack_direction_contact_raw_deg"] = float(attack_direction_raw[contact_i]) if np.isfinite(attack_direction_raw[contact_i]) else np.nan
    out["attack_direction_contact_pull_deg"] = float(attack_direction_pull[contact_i]) if np.isfinite(attack_direction_pull[contact_i]) else np.nan
    contact_x_relative_com_in = (xyz[contact_i, 0] - com_x[contact_i]) * M_TO_IN if np.isfinite(com_x[contact_i]) and np.isfinite(xyz[contact_i, 0]) else np.nan
    valid_com_x = np.isfinite(t) & np.isfinite(com_x)
    rear_window = valid_com_x & (t >= contact - 0.50) & (t <= contact)
    if not rear_window.any():
        rear_window = valid_com_x & (t <= contact)
    if rear_window.any():
        rear_idx_candidates = np.where(rear_window)[0]
        rear_idx = int(rear_idx_candidates[np.nanargmin(com_x[rear_window])])
        preswing_ref_time = float(t[rear_idx])
        preswing_com_x = float(com_x[rear_idx])
    else:
        preswing_ref_time = np.nan
        preswing_com_x = np.nan
    preswing_x_relative_com_in = (xyz[contact_i, 0] - preswing_com_x) * M_TO_IN if np.isfinite(preswing_com_x) and np.isfinite(xyz[contact_i, 0]) else np.nan
    preswing_x_relative_com_in = (xyz[contact_i, 0] - preswing_com_x) * M_TO_IN if np.isfinite(preswing_com_x) and np.isfinite(xyz[contact_i, 0]) else np.nan
    out["contact_barrel_x_relative_com_in"] = float(contact_x_relative_com_in) if np.isfinite(contact_x_relative_com_in) else np.nan
    out["contact_barrel_x_relative_preswing_com_in"] = float(preswing_x_relative_com_in) if np.isfinite(preswing_x_relative_com_in) else np.nan
    out["contact_barrel_preswing_com_reference_ms_before_contact"] = float((contact - preswing_ref_time) * 1000.0) if np.isfinite(preswing_ref_time) else np.nan
    swing_len_m = path_length_between_times(t, xyz, start, contact)
    out["swing_length_lead_hand_onset_to_contact_in"] = float(swing_len_m * M_TO_IN) if np.isfinite(swing_len_m) else np.nan
    out["swing_length_lead_hand_onset_to_contact_ft"] = float(swing_len_m * M_TO_IN / 12.0) if np.isfinite(swing_len_m) else np.nan
    out["swing_path_tilt_contact_deg"] = swing_path_tilt_deg(t, xyz, contact)
    out["attack_angle_contact_in_zone"] = bool(mask[contact_i] and speed_ok[contact_i] and direction_ok[contact_i] and np.isfinite(aa[contact_i]) and IDEAL_MIN_DEG <= aa[contact_i] <= IDEAL_MAX_DEG)
    out["attack_angle_obp_contact_in_zone"] = bool(np.isfinite(obp) and IDEAL_MIN_DEG <= obp <= IDEAL_MAX_DEG)
    out["attack_angle_qc"] = "ok"

    dt = median_dt(t[mask])
    if not np.isfinite(dt) or dt <= 0:
        dt = float(np.nanmedian(np.diff(t[mask])))
    dt_ms = dt * 1000.0 if np.isfinite(dt) else np.nan
    zone_count = int(in_zone.sum())
    total_count = int(mask.sum())
    out["attack_zone_time_ms"] = float(zone_count * dt_ms) if np.isfinite(dt_ms) else np.nan
    out["attack_zone_pct_of_swing"] = float(zone_count / total_count * 100.0) if total_count else np.nan
    out["longest_attack_zone_ms"] = longest_streak_ms(in_zone, t)

    zone_indices = np.where(in_zone)[0]
    depth_in = (xyz[:, 0] - com_x) * M_TO_IN
    y_depth_in = (com_y - xyz[:, 1]) * M_TO_IN
    if len(zone_indices):
        out["attack_zone_entry_ms_before_contact"] = float((contact - t[zone_indices[0]]) * 1000.0)
        out["attack_zone_exit_ms_before_contact"] = float((contact - t[zone_indices[-1]]) * 1000.0)
        out["attack_zone_entry_ms_from_contact"] = float((t[zone_indices[0]] - contact) * 1000.0)
        out["attack_zone_exit_ms_from_contact"] = float((t[zone_indices[-1]] - contact) * 1000.0)
        zone_depth = depth_in[zone_indices]
        out["attack_zone_depth_min_in"] = float(np.nanmin(zone_depth)) if np.isfinite(zone_depth).any() else np.nan
        out["attack_zone_depth_max_toward_pitcher_in"] = float(np.nanmax(zone_depth)) if np.isfinite(zone_depth).any() else np.nan
        out["attack_zone_depth_range_in"] = float(np.nanmax(zone_depth) - np.nanmin(zone_depth)) if np.isfinite(zone_depth).any() else np.nan
        out["attack_zone_depth_entry_in"] = float(depth_in[zone_indices[0]]) if np.isfinite(depth_in[zone_indices[0]]) else np.nan
        out["attack_zone_depth_exit_in"] = float(depth_in[zone_indices[-1]]) if np.isfinite(depth_in[zone_indices[-1]]) else np.nan
        zone_y_depth = y_depth_in[zone_indices]
        out["attack_zone_y_range_relative_com_in"] = float(np.nanmax(zone_y_depth) - np.nanmin(zone_y_depth)) if np.isfinite(zone_y_depth).any() else np.nan
        out["attack_zone_y_min_relative_com_in"] = float(np.nanmin(zone_y_depth)) if np.isfinite(zone_y_depth).any() else np.nan
        out["attack_zone_y_max_relative_com_in"] = float(np.nanmax(zone_y_depth)) if np.isfinite(zone_y_depth).any() else np.nan
        zone_speed = speed[zone_indices]
        out["attack_zone_speed_mean_mph"] = float(np.nanmean(zone_speed) * 2.2369362920544) if np.isfinite(zone_speed).any() else np.nan
        out["attack_zone_speed_max_mph"] = float(np.nanmax(zone_speed) * 2.2369362920544) if np.isfinite(zone_speed).any() else np.nan
        out["attack_zone_speed_pct_max_mean"] = float(np.nanmean(zone_speed / max_window_speed * 100.0)) if np.isfinite(zone_speed).any() and np.isfinite(max_window_speed) and max_window_speed > 0 else np.nan
        out["attack_zone_speed_pct_max_peak"] = float(np.nanmax(zone_speed / max_window_speed * 100.0)) if np.isfinite(zone_speed).any() and np.isfinite(max_window_speed) and max_window_speed > 0 else np.nan
        zone_direction = attack_direction_pull[zone_indices]
        out["attack_direction_zone_mean_pull_deg"] = float(np.nanmean(zone_direction)) if np.isfinite(zone_direction).any() else np.nan
        out["attack_direction_zone_median_pull_deg"] = float(np.nanmedian(zone_direction)) if np.isfinite(zone_direction).any() else np.nan
        out["attack_direction_zone_range_deg"] = float(np.nanmax(zone_direction) - np.nanmin(zone_direction)) if np.isfinite(zone_direction).any() else np.nan
        out["attack_direction_zone_entry_pull_deg"] = float(attack_direction_pull[zone_indices[0]]) if np.isfinite(attack_direction_pull[zone_indices[0]]) else np.nan
        out["attack_direction_zone_exit_pull_deg"] = float(attack_direction_pull[zone_indices[-1]]) if np.isfinite(attack_direction_pull[zone_indices[-1]]) else np.nan
    else:
        out["attack_zone_entry_ms_before_contact"] = np.nan
        out["attack_zone_exit_ms_before_contact"] = np.nan
        out["attack_zone_entry_ms_from_contact"] = np.nan
        out["attack_zone_exit_ms_from_contact"] = np.nan
        out["attack_zone_depth_min_in"] = np.nan
        out["attack_zone_depth_max_toward_pitcher_in"] = np.nan
        out["attack_zone_depth_range_in"] = np.nan
        out["attack_zone_depth_entry_in"] = np.nan
        out["attack_zone_depth_exit_in"] = np.nan
        out["attack_zone_y_range_relative_com_in"] = np.nan
        out["attack_zone_y_min_relative_com_in"] = np.nan
        out["attack_zone_y_max_relative_com_in"] = np.nan
        out["attack_zone_speed_mean_mph"] = np.nan
        out["attack_zone_speed_max_mph"] = np.nan
        out["attack_zone_speed_pct_max_mean"] = np.nan
        out["attack_zone_speed_pct_max_peak"] = np.nan
        out["attack_direction_zone_mean_pull_deg"] = np.nan
        out["attack_direction_zone_median_pull_deg"] = np.nan
        out["attack_direction_zone_range_deg"] = np.nan
        out["attack_direction_zone_entry_pull_deg"] = np.nan
        out["attack_direction_zone_exit_pull_deg"] = np.nan

    window_indices = np.where(mask)[0]
    total_path = 0.0
    zone_path = 0.0
    for a, b in zip(window_indices[:-1], window_indices[1:]):
        dist = float(np.linalg.norm(xyz[b] - xyz[a]))
        if np.isfinite(dist):
            total_path += dist
            if in_zone[a] and in_zone[b]:
                zone_path += dist
    out["attack_zone_path_length_in"] = zone_path * M_TO_IN
    out["attack_window_path_length_in"] = total_path * M_TO_IN
    out["attack_zone_path_pct"] = zone_path / total_path * 100.0 if total_path > 0 else np.nan
    if mask.any():
        window_depth = depth_in[mask]
        out["attack_window_depth_range_in"] = float(np.nanmax(window_depth) - np.nanmin(window_depth)) if np.isfinite(window_depth).any() else np.nan
    else:
        out["attack_window_depth_range_in"] = np.nan
    return out


def longest_streak_ms(mask: np.ndarray, time: np.ndarray) -> float:
    best = 0.0
    current_start = None
    last_i = None
    for i, value in enumerate(mask):
        if value and current_start is None:
            current_start = i
        if not value and current_start is not None:
            last_i = i - 1
            best = max(best, float((time[last_i] - time[current_start]) * 1000.0))
            current_start = None
    if current_start is not None:
        last_i = len(mask) - 1
        best = max(best, float((time[last_i] - time[current_start]) * 1000.0))
    return best


def summarize_metrics(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in [
        "attack_zone_time_ms",
        "attack_angle_contact_bat_speed_mph",
        "swing_length_lead_hand_onset_to_contact_ft",
        "swing_path_tilt_contact_deg",
        "longest_attack_zone_ms",
        "attack_zone_pct_of_swing",
        "attack_zone_path_length_in",
        "attack_zone_path_pct",
        "attack_zone_y_range_relative_com_in",
        "attack_zone_speed_mean_mph",
        "attack_zone_speed_max_mph",
        "attack_zone_speed_pct_max_mean",
        "attack_zone_speed_pct_max_peak",
        "attack_direction_contact_pull_deg",
        "attack_direction_zone_mean_pull_deg",
        "attack_direction_zone_median_pull_deg",
        "attack_direction_zone_range_deg",
        "attack_angle_contact_computed_deg",
        "attack_angle_contact_x",
        "attack_angle_contact_diff_deg",
    ]:
        if col not in data:
            continue
        s = pd.to_numeric(data[col], errors="coerce").dropna()
        rows.append({
            "metric": col,
            "n": len(s),
            "mean": s.mean(),
            "median": s.median(),
            "std": s.std(),
            "p10": s.quantile(0.10),
            "p25": s.quantile(0.25),
            "p75": s.quantile(0.75),
            "p90": s.quantile(0.90),
            "min": s.min(),
            "max": s.max(),
        })
    return pd.DataFrame(rows)


def contact_comparison(data: pd.DataFrame) -> pd.DataFrame:
    d = data[["attack_angle_contact_computed_deg", "attack_angle_contact_x", "attack_angle_contact_xz_deg"]].replace([np.inf, -np.inf], np.nan).dropna()
    rows = []
    for computed_col in ["attack_angle_contact_computed_deg", "attack_angle_contact_xz_deg"]:
        if d.empty:
            continue
        diff = d[computed_col] - d["attack_angle_contact_x"]
        rows.append({
            "computed_col": computed_col,
            "n": len(d),
            "pearson_r_vs_obp": d[computed_col].corr(d["attack_angle_contact_x"]),
            "mean_diff_computed_minus_obp": diff.mean(),
            "median_abs_diff": diff.abs().median(),
            "rmse_diff": float(np.sqrt(np.nanmean(diff * diff))),
        })
    return pd.DataFrame(rows)


def make_hitter_summary(data: pd.DataFrame) -> pd.DataFrame:
    d = data[data["attack_angle_qc"].eq("ok")].copy()
    grouped = d.groupby("user", as_index=False).agg(
        swing_count=("session_swing", "count"),
        median_attack_zone_time_ms=("attack_zone_time_ms", "median"),
        mean_attack_zone_time_ms=("attack_zone_time_ms", "mean"),
        std_attack_zone_time_ms=("attack_zone_time_ms", "std"),
        median_longest_attack_zone_ms=("longest_attack_zone_ms", "median"),
        median_attack_zone_pct=("attack_zone_pct_of_swing", "median"),
        median_attack_zone_path_in=("attack_zone_path_length_in", "median"),
        pct_contact_computed_in_zone=("attack_angle_contact_in_zone", "mean"),
        median_bat_speed_mph=("bat_speed_mph_max_x", "median"),
    )
    grouped["pct_contact_computed_in_zone"] *= 100.0
    return grouped.sort_values(["median_attack_zone_time_ms", "median_longest_attack_zone_ms"], ascending=False)


def plot_distributions(data: pd.DataFrame) -> None:
    specs = [
        ("attack_zone_time_ms", "Total Time in 5-20 Degree Attack-Angle Zone", "ms", "attack_zone_time_distribution.png", True),
        ("attack_zone_y_range_relative_com_in", "In-Zone Sweet-Spot Y Range Relative to COM", "inches", "attack_zone_y_range_relative_com_distribution.png", True),
    ]

    def tight_bins(series: pd.Series, start_at_zero: bool) -> np.ndarray:
        values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
        if len(values) == 0:
            return np.linspace(0, 1, 20)
        lo = 0.0 if start_at_zero and np.nanmin(values) >= 0 else float(np.nanmin(values))
        hi = float(np.nanmax(values))
        if np.isclose(lo, hi):
            hi = lo + 1.0
        pad = (hi - lo) * 0.06
        lower = 0.0 if start_at_zero and lo == 0.0 else lo - pad
        upper = hi + pad
        return np.linspace(lower, upper, 28)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8))
    for ax, (col, title, xlabel, _, start_at_zero) in zip(axes.ravel(), specs):
        s = pd.to_numeric(data[col], errors="coerce").dropna()
        bins = tight_bins(s, start_at_zero)
        ax.hist(s, bins=bins, color="#2563eb", alpha=0.78)
        ax.axvline(s.median(), color="#111827", ls="--", lw=1.7, label=f"median {s.median():.1f}")
        ax.axvline(s.mean(), color="#f59e0b", ls=":", lw=1.7, label=f"mean {s.mean():.1f}")
        ax.set_xlim(bins[0], bins[-1])
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("swings")
        ax.grid(True, alpha=.2)
        ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "attack_angle_zone_distributions.png", dpi=180)
    plt.close(fig)
    for col, title, xlabel, filename, start_at_zero in specs:
        s = pd.to_numeric(data[col], errors="coerce").dropna()
        bins = tight_bins(s, start_at_zero)
        fig, ax = plt.subplots(figsize=(10, 5.8))
        ax.hist(s, bins=bins, color="#2563eb", alpha=0.78)
        ax.axvline(s.median(), color="#111827", ls="--", lw=1.7, label=f"median {s.median():.1f}")
        ax.axvline(s.mean(), color="#f59e0b", ls=":", lw=1.7, label=f"mean {s.mean():.1f}")
        ax.set_xlim(bins[0], bins[-1])
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("swings")
        ax.grid(True, alpha=.2)
        ax.legend()
        fig.tight_layout()
        fig.savefig(FIG_DIR / filename, dpi=180)
        plt.close(fig)


def plot_contact_comparison(data: pd.DataFrame) -> None:
    d = data[["attack_angle_contact_computed_deg", "attack_angle_contact_x", "attack_angle_contact_xz_deg"]].replace([np.inf, -np.inf], np.nan).dropna()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    for ax, col, title in [
        (axes[0], "attack_angle_contact_computed_deg", "Computed side-view x/z vs OBP/Blast contact"),
        (axes[1], "attack_angle_contact_xz_deg", "Side-view x/z duplicate check vs OBP/Blast contact"),
    ]:
        ax.scatter(d["attack_angle_contact_x"], d[col], s=22, alpha=.5, color="#2563eb")
        lo = np.nanmin([d["attack_angle_contact_x"].min(), d[col].min()])
        hi = np.nanmax([d["attack_angle_contact_x"].max(), d[col].max()])
        ax.plot([lo, hi], [lo, hi], color="#111827", ls="--", lw=1)
        ax.axvspan(IDEAL_MIN_DEG, IDEAL_MAX_DEG, color="#ef4444", alpha=.08)
        ax.axhspan(IDEAL_MIN_DEG, IDEAL_MAX_DEG, color="#ef4444", alpha=.08)
        ax.set_title(title)
        ax.set_xlabel("OBP/Blast attack_angle_contact_x (deg)")
        ax.set_ylabel("computed attack angle at contact (deg)")
        ax.grid(True, alpha=.2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "attack_angle_contact_comparison.png", dpi=180)
    plt.close(fig)


def plot_top_hitters(hitter_summary: pd.DataFrame) -> None:
    top = hitter_summary[hitter_summary["swing_count"] >= 3].head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, max(5, 0.35 * len(top))))
    labels = [f"User {int(u)}" for u in top["user"]]
    ax.barh(labels, top["median_attack_zone_time_ms"], color="#2563eb", alpha=.82)
    ax.set_title("Top Hitters by Median Time in 5-20? Attack-Angle Zone")
    ax.set_xlabel("median zone time (ms)")
    ax.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "top_hitters_attack_zone_time.png", dpi=180)
    plt.close(fig)


def choose_examples(data: pd.DataFrame) -> pd.DataFrame:
    d = data[data["attack_angle_qc"].eq("ok")].copy()
    picks = []
    def add(label: str, sub: pd.DataFrame) -> None:
        for _, row in sub.iterrows():
            r = row.copy()
            r["example_type"] = label
            picks.append(r)
    add("highest_zone_time", d.nlargest(3, "attack_zone_time_ms"))
    add("lowest_zone_time", d.nsmallest(3, "attack_zone_time_ms"))
    med = d["attack_zone_time_ms"].median()
    add("near_median_zone_time", d.assign(dist=(d["attack_zone_time_ms"] - med).abs()).nsmallest(3, "dist"))
    add("longest_continuous_zone", d.nlargest(3, "longest_attack_zone_ms"))
    return pd.DataFrame(picks).drop_duplicates("session_swing", keep="first").head(12)


def nearest_payload_frame(frames: list[dict], time_value: float) -> int:
    if not frames or not np.isfinite(time_value):
        return 0
    return int(np.nanargmin([abs(float(frame.get("time", np.nan)) - time_value) for frame in frames]))


def set_attack_viewer_event_groups(payload: dict, velocity: pd.Series, contact_time: float) -> None:
    force_order = {"force climb start": 0, "fp10": 1, "fp100": 2, "peak force": 3}
    onset_order = {"pelvis onset": 0, "torso onset": 1, "lead hand onset": 2}
    max_velocity_specs = [
        ("pelvis max velocity", "pelvis_velocity20_peak_ms_before_contact", "#8e44ad", 0),
        ("torso max velocity", "torso_velocity20_peak_ms_before_contact", "#2980b9", 1),
        ("lead hand max velocity", "lead_hand_velocity20_peak_ms_before_contact", "#0984e3", 2),
    ]
    events = []
    for event in payload.get("events", []):
        name = str(event.get("name", ""))
        if name == "lead arm onset":
            continue
        if name in force_order:
            event["group"] = "Force"
            event["groupOrder"] = 0
            event["order"] = force_order[name]
        elif name in onset_order:
            event["group"] = "Onset"
            event["groupOrder"] = 1
            event["order"] = onset_order[name]
        elif name == "contact":
            event["group"] = "Contact"
            event["groupOrder"] = 3
            event["order"] = 0
        else:
            event["group"] = "Other"
            event["groupOrder"] = 9
            event["order"] = 0
        events.append(event)

    for label, col, color, order in max_velocity_specs:
        ms_before = pd.to_numeric(pd.Series([velocity.get(col)]), errors="coerce").iloc[0]
        if not np.isfinite(ms_before) or not np.isfinite(contact_time):
            continue
        event_time = float(contact_time - ms_before / 1000.0)
        events.append({
            "name": label,
            "time": clean_float(event_time),
            "relativeMs": clean_float(-float(ms_before)),
            "frame": nearest_payload_frame(payload.get("frames", []), event_time),
            "color": color,
            "group": "Max Velocity",
            "groupOrder": 2,
            "order": order,
        })
    payload["events"] = events


def make_velocity20_onset_row(current: pd.Series, velocity: pd.Series, contact_time: float) -> pd.Series:
    row = current.copy()
    row["contact_time"] = contact_time
    mapping = {
        "pelvis": ("pelvis_velocity20_onset_time", "pelvis_velocity20_to_contact_ms"),
        "torso": ("torso_velocity20_onset_time", "torso_velocity20_to_contact_ms"),
        "lead_hand": ("lead_hand_velocity20_onset_time", "lead_hand_velocity20_to_contact_ms"),
    }
    for segment, (time_col, ms_col) in mapping.items():
        onset_time = pd.to_numeric(pd.Series([velocity.get(time_col)]), errors="coerce").iloc[0]
        to_contact = pd.to_numeric(pd.Series([velocity.get(ms_col)]), errors="coerce").iloc[0]
        row[f"{segment}_onset_time"] = onset_time
        row[f"{segment}_inflection_time"] = onset_time
        row[f"{segment}_to_contact_ms"] = to_contact
        row[f"{segment}_inflection_to_contact_ms"] = to_contact
        row[f"{segment}_onset_method"] = f"velocity20_primary_{segment}"
    row["composite_swing_time_ms"] = velocity.get("velocity20_composite_swing_time_ms")
    row["initiation_spread_ms"] = velocity.get("velocity20_initiation_spread_ms")
    row["onset_qc"] = "velocity20_primary_with_attack_angle_zone"
    return row


def attack_payload_for_frames(landmarks: pd.DataFrame, payload: dict, metrics_row: pd.Series) -> dict:
    series = compute_attack_series(landmarks)
    samples = []
    if not series.get("ok"):
        return {"samples": samples, "idealMinDeg": IDEAL_MIN_DEG, "idealMaxDeg": IDEAL_MAX_DEG}
    t = np.asarray(series["time"], dtype=float)
    raw_aa = np.asarray(series["attack_3d"], dtype=float)
    raw_speed = np.asarray(series["speed"], dtype=float)
    raw_vx = np.asarray(series.get("vx", np.full_like(t, np.nan)), dtype=float)
    raw_vy = np.asarray(series.get("vy", np.full_like(t, np.nan)), dtype=float)
    raw_xyz = np.asarray(series.get("xyz", np.full((len(t), 3), np.nan)), dtype=float)
    raw_com_x = np.asarray(series.get("com_x", np.full_like(t, np.nan)), dtype=float)
    raw_x_depth_in = (raw_xyz[:, 0] - raw_com_x) * M_TO_IN if raw_xyz.ndim == 2 and raw_xyz.shape[1] >= 1 else np.full_like(t, np.nan)
    direction_sign = -1.0 if str(payload.get("hitterSide", "")).upper() == "L" else 1.0
    contact = float(payload["contactTime"])
    window_start_ms = pd.to_numeric(pd.Series([metrics_row.get("attack_angle_window_start_ms_before_contact")]), errors="coerce").iloc[0]
    start_time = contact - window_start_ms / 1000.0 if np.isfinite(window_start_ms) else contact - 0.20
    max_window_speed = pd.to_numeric(pd.Series([metrics_row.get("attack_angle_max_window_speed_mps")]), errors="coerce").iloc[0]
    window_end_ms_after_contact = pd.to_numeric(pd.Series([metrics_row.get("attack_angle_window_end_ms_after_contact")]), errors="coerce").iloc[0]
    end_time = contact + window_end_ms_after_contact / 1000.0 if np.isfinite(window_end_ms_after_contact) else contact + ATTACK_ZONE_AFTER_CONTACT_S
    frame_times = np.array([float(frame["time"]) for frame in payload["frames"]], dtype=float)
    corrected_speed = interpolate_series_at_times(t, raw_speed, frame_times + MARKER_AA_TIME_OFFSET_S)
    if not np.isfinite(max_window_speed):
        window_mask = (frame_times >= start_time) & (frame_times <= end_time) & np.isfinite(corrected_speed)
        max_window_speed = float(np.nanmax(corrected_speed[window_mask])) if window_mask.any() else np.nan
    speed_gate = pd.to_numeric(pd.Series([metrics_row.get("attack_angle_speed_gate_mps")]), errors="coerce").iloc[0]
    if not np.isfinite(speed_gate) and np.isfinite(max_window_speed):
        speed_gate = max_window_speed * ATTACK_ZONE_MIN_SPEED_PCT
    frame_zone_flags = []
    for frame in payload["frames"]:
        ft = float(frame["time"])
        query_time = ft + MARKER_AA_TIME_OFFSET_S
        angle_arr = interpolate_series_at_times(t, raw_aa, np.array([query_time], dtype=float))
        speed_arr = interpolate_series_at_times(t, raw_speed, np.array([query_time], dtype=float))
        vx_arr = interpolate_series_at_times(t, raw_vx, np.array([query_time], dtype=float))
        vy_arr = interpolate_series_at_times(t, raw_vy, np.array([query_time], dtype=float))
        x_depth_arr = interpolate_series_at_times(t, raw_x_depth_in, np.array([ft], dtype=float))
        angle = float(angle_arr[0]) if np.isfinite(angle_arr[0]) else np.nan
        frame_speed = float(speed_arr[0]) if np.isfinite(speed_arr[0]) else np.nan
        direction = float(np.degrees(np.arctan2(vy_arr[0], abs(vx_arr[0]))) * direction_sign) if np.isfinite(vx_arr[0]) and np.isfinite(vy_arr[0]) else np.nan
        x_depth = float(x_depth_arr[0]) if np.isfinite(x_depth_arr[0]) else np.nan
        speed_pct = frame_speed / max_window_speed if np.isfinite(frame_speed) and np.isfinite(max_window_speed) and max_window_speed > 0 else np.nan
        passes_speed_gate = bool(np.isfinite(frame_speed) and np.isfinite(speed_gate) and frame_speed >= speed_gate)
        in_window = bool(start_time <= ft <= end_time)
        direction_ok = bool(np.isfinite(direction))
        in_zone = bool(in_window and passes_speed_gate and direction_ok and np.isfinite(angle) and IDEAL_MIN_DEG <= angle <= IDEAL_MAX_DEG)
        frame_zone_flags.append(in_zone)
        samples.append({
            "attackAngleDeg": clean_float(angle),
            "attackDirectionDeg": clean_float(direction),
            "sweetSpotSpeedMps": clean_float(frame_speed),
            "sweetSpotSpeedPctMax": clean_float(speed_pct),
            "barrelXRelativeComIn": clean_float(x_depth),
            "passesSpeedGate": passes_speed_gate,
            "passesDirectionGate": direction_ok,
            "inSwingWindow": in_window,
            "inIdealZone": in_zone,
        })
    relevant_zone = keep_zone_segment_nearest_contact(np.asarray(frame_zone_flags, dtype=bool), frame_times, contact)
    for sample, keep in zip(samples, relevant_zone):
        sample["inIdealZone"] = bool(keep)
    return {
        "samples": samples,
        "idealMinDeg": IDEAL_MIN_DEG,
        "idealMaxDeg": IDEAL_MAX_DEG,
        "speedGatePct": ATTACK_ZONE_MIN_SPEED_PCT,
        "speedGateMps": clean_float(speed_gate),
        "attackDirectionWindowEndDeg": clean_float(ATTACK_DIRECTION_WINDOW_END_DEG),
        "maxWindowSpeedMps": clean_float(max_window_speed),
        "windowStartMsBeforeContact": clean_float(window_start_ms),
        "windowEndMsAfterContact": clean_float(window_end_ms_after_contact),
        "markerTimeOffsetMs": clean_float(MARKER_AA_TIME_OFFSET_S * 1000.0),
    }


def write_attack_viewers(examples: pd.DataFrame, landmarks: pd.DataFrame, manifest: pd.DataFrame, current_onsets: pd.DataFrame, metadata: pd.DataFrame, velocity20: pd.DataFrame, paths: dict[str, Path]) -> None:
    joint_velos = read_zipped_csv(paths["joint_velos"], set(examples["session_swing"].astype(str)), required=False)
    joint_velos["session_swing"] = joint_velos["session_swing"].astype(str)
    for df in [manifest, current_onsets, metadata, velocity20]:
        df["session_swing"] = df["session_swing"].astype(str)
    links = []
    for _, ex in examples.iterrows():
        sid = str(ex["session_swing"])
        swing_landmarks = landmarks.loc[landmarks["session_swing"].astype(str).eq(sid)]
        current = current_onsets.loc[current_onsets["session_swing"].eq(sid)]
        man = manifest.loc[manifest["session_swing"].eq(sid)]
        meta = metadata.loc[metadata["session_swing"].eq(sid)]
        vel = velocity20.loc[velocity20["session_swing"].eq(sid)]
        if swing_landmarks.empty or current.empty or man.empty or vel.empty:
            continue
        contact = float(man.iloc[0]["contact_time"])
        onset_row = make_velocity20_onset_row(current.iloc[0], vel.iloc[0], contact)
        payload = build_payload(
            sid,
            swing_landmarks,
            onset_row,
            man.iloc[0],
            meta.iloc[0] if not meta.empty else None,
            joint_velos.loc[joint_velos["session_swing"].astype(str).eq(sid)] if not joint_velos.empty else joint_velos,
            0.55,
            0.10,
        )
        payload["sessionSwing"] = sid
        payload["attackAngle"] = attack_payload_for_frames(swing_landmarks, payload, ex)
        set_attack_viewer_event_groups(payload, vel.iloc[0], contact)
        payload["tracers"] = [tracer for tracer in payload.get("tracers", []) if tracer.get("pointKey") != "back_elbow"]
        payload["searchWindows"] = []
        payload["viewerOptions"] = {
            "displayTitle": sid,
            "subtitle": "",
            "hideMetrics": True,
            "hideSearchWindows": True,
            "hideAccelerationVectors": True,
            "hidePointLegend": True,
            "hidePointKeys": ["thorax_top", "thorax_bottom", "left_wrist", "right_wrist"],
            "singleLandmarkColor": "#95a5a6",
            "definitionHref": "definitions.html",
            "noteText": "Timeline marks show detected events. Red barrel ribbon marks the selected contact-relevant attack-angle segment.",
            "methodologyNote": "Contact bat speed and attack angle were recomputed frame-by-frame from marker data to build this viewer. Small differences from OBP contact fields were expected because OBP's processed contact metrics were not available across the full swing path.",
        }
        keep_meta = [
            "user", "session", "hitter_side", "highest_playing_level",
            "session_height_in", "session_mass_lbs",
            "attack_angle_contact_x",
        ]
        payload["metadata"] = {key: payload.get("metadata", {}).get(key) for key in keep_meta if key in payload.get("metadata", {})}
        payload["contactMetrics"] = {
            "bat_speed": {"label": "Bat Speed", "value": clean_float(ex.get("attack_angle_contact_bat_speed_mph")), "units": "mph"},
            "attack_angle": {"label": "Attack Angle", "value": clean_float(ex.get("attack_angle_contact_computed_deg")), "units": "deg"},
            "attack_direction": {"label": "Attack Direction", "value": clean_float(ex.get("attack_direction_contact_pull_deg")), "units": "deg"},
            "swing_length": {"label": "Swing Length", "value": clean_float(ex.get("swing_length_lead_hand_onset_to_contact_ft")), "units": "ft"},
            "swing_path_tilt": {"label": "Swing Path Tilt", "value": clean_float(ex.get("swing_path_tilt_contact_deg")), "units": "deg"},
            "contact_x_relative_com": {"label": "Out Front (Contact COM)", "value": clean_float(ex.get("contact_barrel_x_relative_com_in")), "units": "in"},
            "contact_x_relative_preswing_com": {"label": "Out Front (Rear-most COM)", "value": clean_float(ex.get("contact_barrel_x_relative_preswing_com_in")), "units": "in"},
        }
        for key in [
            "attack_zone_time_ms", "longest_attack_zone_ms", "attack_zone_pct_of_swing",
            "attack_zone_path_length_in", "attack_zone_path_pct", "attack_angle_contact_computed_deg",
            "attack_angle_contact_x", "attack_angle_contact_diff_deg", "attack_angle_contact_bat_speed_mph",
            "swing_length_lead_hand_onset_to_contact_in", "swing_length_lead_hand_onset_to_contact_ft", "swing_path_tilt_contact_deg",
            "contact_barrel_x_relative_com_in", "contact_barrel_x_relative_preswing_com_in",
            "contact_barrel_preswing_com_reference_ms_before_contact",
            "attack_angle_window_start_ms_before_contact",
            "attack_angle_speed_gate_pct", "attack_angle_speed_gate_mps", "attack_angle_max_window_speed_mps",
            "attack_angle_window_end_ms_after_contact", "attack_angle_window_end_ms_before_contact",
            "attack_angle_window_end_attack_direction_deg", "attack_angle_marker_time_offset_ms",
            "attack_zone_y_range_relative_com_in", "attack_zone_speed_mean_mph",
            "attack_zone_speed_max_mph", "attack_zone_speed_pct_max_mean",
            "attack_zone_speed_pct_max_peak", "attack_direction_contact_pull_deg",
            "attack_direction_zone_mean_pull_deg", "attack_direction_zone_median_pull_deg",
            "attack_direction_zone_range_deg",
        ]:
            if key in ex:
                payload["metrics"][key] = clean_float(ex.get(key))
        html = render_html(payload).replace(
            "Scrub frame by frame to verify whether detected onsets and contact look intuitive.",
            "Attack-angle zone viewer: red barrel trace segments show frames where timing-corrected computed sweet-spot attack angle is between 5 and 20 degrees inside the lead-hand-onset to +55 degree pull attack-direction window.",
        )
        output = VIEWER_DIR / f"{sid}.html"
        output.write_text(html, encoding="utf-8")
        links.append((sid, output.name, ex))
    write_definitions_page()
    write_index(links)


def clean_float(value: object) -> float | None:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if np.isfinite(f) else None


def write_definitions_page() -> None:
    html = """<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Swing Viewer Definitions</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:32px auto;max-width:960px;color:#172033;line-height:1.55;background:#f8fafc}
main{background:#fff;border:1px solid #d7deea;border-radius:8px;padding:28px}
h1{margin-top:0}h2{margin-top:28px}dt{font-weight:700;margin-top:16px}dd{margin:4px 0 0 0;color:#40516a}.muted{color:#64748b}.pill{display:inline-block;background:#eef4ff;color:#1d4ed8;border-radius:999px;padding:2px 8px;font-size:12px;font-weight:700}ul{margin-top:6px;color:#40516a}
</style>
</head>
<body><main>
<h1>Swing Viewer Definitions</h1>
<p class='muted'>These definitions described the current attack-angle swing viewers. Times were shown relative to contact, where negative values occurred before contact and 0.0 ms represented contact.</p>

<h2>Event Times</h2>
<dl>
<dt>Force climb start</dt><dd>The estimated start of the lead-leg force rise. The force curve was smoothed, then the algorithm looked for the final quiet baseline or local minimum before FP100. Climb start was marked once force rose 5 percentage points of bodyweight above that local baseline. This was intended to capture the start of the meaningful force climb rather than early toe-touch noise.</dd>
<dt>FP10</dt><dd>The lead force crossing 10% bodyweight. Upward crossings after the late pre-contact cutoff were ignored so that small changes near/after contact did not become the selected FP10.</dd>
<dt>FP100</dt><dd>The lead force crossing 100% bodyweight. The selected event was the relevant upward crossing before the late pre-contact cutoff, rather than an unrelated post-contact crossing.</dd>
<dt>Peak force</dt><dd>The selected maximum lead force for the swing after force quality-control decisions. Negative pre-contact force baselines were handled by reporting corrected force range when needed, and known unusable force swings were excluded from force-specific interpretation.</dd>
<dt>Pelvis onset</dt><dd>The pelvis onset was based on the pelvis 3D angular velocity magnitude. The max pelvis velocity reference was found, and onset was marked at the latest upward crossing of 20% of that max velocity that led into the selected velocity ramp.</dd>
<dt>Torso onset</dt><dd>The torso onset used the same velocity-threshold concept as the pelvis: 3D torso angular velocity magnitude was smoothed, the max velocity reference was identified, and onset was marked at the 20% upward crossing into that ramp.</dd>
<dt>Lead hand onset</dt><dd>The lead hand onset used 3D lead-hand angular velocity magnitude before contact. The max pre-contact lead-hand velocity reference was identified, and onset was marked at the 20% upward crossing into that selected hand-speed ramp.</dd>
<dt>Pelvis, torso, lead hand max velocity</dt><dd>These events marked the frames where each segment reached the max angular velocity reference used by the 20% onset calculation.</dd>
<dt>Contact</dt><dd>The OBP contact event for the swing.</dd>
</dl>

<h2>Trace Readouts</h2>
<dl>
<dt>AA <span class='pill'>Attack Angle</span></dt><dd>The vertical direction of the sweet spot's velocity relative to the ground. A value of 0 degrees meant the sweet spot moved parallel to the ground; positive values meant the sweet spot moved upward. The viewer used the timing-corrected marker-derived sweet-spot velocity.</dd>
<dt>AD <span class='pill'>Attack Direction</span></dt><dd>The horizontal direction of the sweet spot's velocity. Pull-side direction was positive, opposite-field direction was negative, and values near 0 degrees represented a middle-field direction.</dd>
<dt>Bat Speed</dt><dd>The current sweet-spot speed in mph at the displayed frame. The percentage was relative to that swing's max sweet-spot speed inside the attack-angle swing window. The gate was 30% of that max speed.</dd>
<dt>Attack-angle swing window</dt><dd>The attack-angle window started at the lead hand onset. It ended at the latest upward crossing of +55 degrees pull-side attack direction after lead hand onset. The +55 degree endpoint was used as a practical boundary for the part of the swing that could still plausibly do damage, rather than including the finish. If +55 degrees was not reached, the fallback endpoint was 100 ms after contact.</dd>
<dt>Ideal attack-angle zone</dt><dd>The red ribbon appeared when all of the following were true: attack angle was inside the selected range, sweet-spot speed passed the 30% speed gate, the frame was inside the lead-hand-onset-to-55-degree attack-direction swing window, and the zone segment was the contact-relevant segment nearest contact.</dd>
<dt>Ideal zone time</dt><dd>Total milliseconds spent in the currently selected ideal attack-angle range after the same swing-window and speed-gate filters were applied. The viewer also reported the ideal-zone COM-to-barrel out-front range for that selected segment. In the OBP coordinate system, the pitcher direction is +X, so this used sweet-spot X minus center-of-mass X and converted the result to inches. Positive values meant the barrel was in front of the COM toward the pitcher; negative values meant it was behind the COM toward the catcher. This was a dynamic, frame-by-frame COM reference.</dd>
<dt>Optimal range occurred during contact</dt><dd>A Yes/No marker indicating whether the frame closest to contact satisfied the same ideal-zone conditions used for the ribbon.</dd>
<dt>Segment angular velocity</dt><dd>The pelvis, torso, and lead hand trace readouts showed current 3D angular velocity magnitude in degrees per second and the percentage of that segment's max reference velocity.</dd>
</dl>

<h2>Contact Metrics</h2>
<p class='muted'>The contact metrics table reported values at the contact frame.</p>
<dl>
<dt>OBP validation fields</dt><dd>OBP provided official contact bat speed and contact attack angle fields. The viewer's marker-derived bat speed and attack angle were validated against those OBP contact fields.</dd>
<dt>Frame-by-frame marker calculations</dt><dd>Bat speed and attack angle used the same contact-level concepts as the OBP variables, but the viewer recomputed sweet-spot velocity from marker positions so those values could be shown across the full swing path. Small differences from OBP's processed contact values were expected.</dd>
<dt>Project-derived contact metrics</dt><dd>Attack direction, swing length, and swing path tilt were project-derived metrics because matching OBP/Blast reference fields were not available.</dd>
<dt>Swing length</dt><dd>Swing length was measured as sweet-spot path length from lead hand onset to contact and was displayed in feet.</dd>
<dt>Swing path tilt</dt><dd>Swing path tilt followed the Statcast-style concept of fitting the swing plane from the sweet-spot path over the 40 ms before contact and reporting that plane's angle relative to the ground.</dd>
<dt>Out Front (Contact COM)</dt><dd>This used the sweet spot at contact minus the hitter's COM at contact in OBP +X. It behaved like a dynamic extension/depth-at-impact measure.</dd>
<dt>Out Front (Rear-most COM)</dt><dd>This used the same contact sweet-spot position but compared it with the hitter's furthest catcher-side COM position from 500 ms before contact through contact. In OBP coordinates, +X pointed toward the pitcher, so the rear-most COM was the lowest COM X value in that window. This normalized hitters who were still drifting backward or already moving forward at exactly -500 ms.</dd>
<dt>Coordinate note</dt><dd>Baseball Savant labels its mound-to-plate CSV direction as Y, while OBP labels the pitcher direction as X, so the axis names were not directly interchangeable.</dd>
<dt>Interpretation note</dt><dd>Neither out-front metric represented total arm extension on inside/outside pitch locations; both measured only mound-direction depth.</dd>
</dl>

<h2>Viewer Controls</h2>
<p>The Ideal AA boxes changed the attack-angle range shown by the ribbon and zone-time summary inside the open HTML file. The saved dataset metrics remained based on the default 5-20 degree range unless the Python analysis was rerun with different constants.</p>
<p>The percentage shown beside ideal zone time represented ideal-zone time divided by total attack-angle swing-window time.</p>
</main></body></html>"""
    (VIEWER_DIR / "definitions.html").write_text(html, encoding="utf-8")


def write_index(links: list[tuple[str, str, pd.Series]]) -> None:
    rows = []
    for sid, filename, row in links:
        rows.append(
            f"<tr><td><a href='{filename}'>{sid}</a></td><td>{row.get('example_type')}</td>"
            f"<td>{float(row.get('attack_zone_time_ms')):.1f}</td>"
            f"<td>{float(row.get('longest_attack_zone_ms')):.1f}</td>"
            f"<td>{float(row.get('attack_zone_pct_of_swing')):.1f}%</td>"
            f"<td>{float(row.get('attack_angle_contact_computed_deg')):.1f}</td></tr>"
        )
    html = """<!doctype html><html><head><meta charset='utf-8'><title>Attack Angle Zone QC Viewers</title>
<style>body{font-family:Arial,sans-serif;margin:32px;color:#172033}table{border-collapse:collapse}td,th{border-bottom:1px solid #d7deea;padding:8px 12px;text-align:left}th{background:#f4f7fb}</style></head><body>
<h1>Attack Angle Zone QC Viewers</h1>
<p>Translucent red ribbon marks frames where timing-corrected sweet-spot attack angle is between 5 and 20 degrees while sweet-spot speed is at least 30% of its swing-window maximum. The window runs from lead hand onset to the latest upward crossing of +55 degrees pull-side attack direction.</p>
<table><thead><tr><th>swing</th><th>example type</th><th>zone time ms</th><th>longest streak ms</th><th>zone pct</th><th>computed contact AA</th></tr></thead><tbody>
""" + "\n".join(rows) + "\n</tbody></table></body></html>"
    (VIEWER_DIR / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())















