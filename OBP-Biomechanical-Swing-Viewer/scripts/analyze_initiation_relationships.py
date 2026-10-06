from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from obp_swing_time.pipeline import (  # noqa: E402
    PRIMARY_CONFIG,
    expected_paths,
    first_numeric,
    median_dt,
    read_zipped_csv,
    smooth_positions,
)


SEGMENTS = ["pelvis", "torso", "lead_hand"]
ONSET_TIE_TOLERANCE_S = 0.0015
SEGMENT_LABELS = {
    "pelvis": "Pelvis",
    "torso": "Torso",
    "lead_arm": "Lead Arm",
    "lead_hand": "Lead Hand",
}
PITCH_SPEED_FALLBACK_MPH = 65.0
M_TO_FT = 3.280839895


def main() -> int:
    out_dir = PROJECT_ROOT / "outputs" / "initiation_analysis"
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(PROJECT_ROOT / "outputs" / "model_dataset.csv")
    data["session_swing"] = data["session_swing"].astype(str)
    data = add_onset_sequence_metrics(data)
    data = add_squared_up_metrics(data)

    print("Calculating swing length from barrel path inflection...")
    data_root = Path(r"E:\Baseball\Data\OBP")
    paths = expected_paths(data_root)
    selected = set(data["session_swing"].dropna().astype(str))
    landmarks = read_zipped_csv(paths["landmarks"], selected)
    swing_length = calculate_swing_lengths(landmarks)
    data = data.merge(swing_length, on="session_swing", how="left")

    data.to_csv(out_dir / "initiation_analysis_dataset.csv", index=False)

    regression_rows = []
    regression_rows.append(
        fit_regression(
            data,
            y="bat_speed_mph_max_x",
            x="initiation_spread_ms",
            label="bat_speed_max_vs_initiation_spread",
        )
    )
    regression_rows.append(
        fit_regression(
            data,
            y="swing_length_from_barrel_inflection_ft",
            x="initiation_spread_ms",
            label="swing_length_vs_initiation_spread",
        )
    )
    regression_rows.append(
        fit_regression(
            data,
            y="squared_up_pct",
            x="initiation_spread_ms",
            label="squared_up_pct_vs_initiation_spread",
        )
    )
    regression_rows.append(
        fit_regression(
            data,
            y="bat_speed_mph_max_x",
            x="onset_order_score",
            label="bat_speed_max_vs_onset_order_score",
        )
    )
    regression_rows.append(
        fit_logistic(
            data,
            y="squared_up_90plus",
            x="initiation_spread_ms",
            label="squared_up_90plus_vs_initiation_spread",
        )
    )
    regressions = pd.DataFrame(regression_rows)
    regressions.to_csv(out_dir / "regression_summary.csv", index=False)

    order_dist = make_order_distribution(data, out_dir)
    order_dist.to_csv(out_dir / "onset_order_distribution.csv", index=False)
    missing_key_points = make_missing_key_point_table(data)
    missing_key_points.to_csv(out_dir / "missing_key_point_onsets.csv", index=False)

    plot_initiation_spread_distribution(data, fig_dir)
    plot_onset_timing_distributions(data, fig_dir)
    plot_initiation_spread_by_missing_pattern(data, fig_dir)
    plot_bat_speed_vs_spread(data, fig_dir)
    plot_swing_length_vs_spread(data, fig_dir)
    plot_onset_order_distribution(order_dist, fig_dir)
    plot_bat_speed_by_onset_order(data, order_dist, fig_dir)
    plot_squared_up_vs_spread(data, fig_dir)

    report = write_report(data, regressions, order_dist, missing_key_points, out_dir, fig_dir)
    print(out_dir / "initiation_analysis_dataset.csv")
    print(out_dir / "regression_summary.csv")
    print(out_dir / "onset_order_distribution.csv")
    print(out_dir / "missing_key_point_onsets.csv")
    print(report)
    return 0


def add_onset_sequence_metrics(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    orders = []
    scores = []
    ranges = []
    for _, row in out.iterrows():
        pairs = []
        for segment in SEGMENTS:
            val = pd.to_numeric(pd.Series([row.get(f"{segment}_onset_time")]), errors="coerce").iloc[0]
            if np.isfinite(val):
                pairs.append((float(val), segment))
        pairs = sorted(pairs)
        order, positions = format_onset_order(pairs)
        orders.append(order)
        scores.append(score_onset_order(positions))
        vals = [val for val, _ in pairs]
        ranges.append((max(vals) - min(vals)) * 1000.0 if len(vals) >= 2 else np.nan)
    out["onset_order"] = orders
    out["onset_order_score"] = scores
    out["onset_order_range_ms_check"] = ranges
    return out


def format_onset_order(pairs: list[tuple[float, str]]) -> tuple[str, dict[str, int]]:
    groups: list[list[tuple[float, str]]] = []
    for value, segment in pairs:
        if groups and abs(value - groups[-1][0][0]) <= ONSET_TIE_TOLERANCE_S:
            groups[-1].append((value, segment))
        else:
            groups.append([(value, segment)])

    labels = []
    positions = {}
    for group_i, group in enumerate(groups):
        segments = [segment for _, segment in group]
        labels.append("=".join(segments))
        for segment in segments:
            positions[segment] = group_i
    return ">".join(labels), positions


def score_onset_order(positions: dict[str, int]) -> int:
    target = ["pelvis", "torso", "lead_hand"]
    score = 0
    for a, b in zip(target, target[1:]):
        if a in positions and b in positions and positions[a] < positions[b]:
            score += 1
    return score


def add_squared_up_metrics(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    out["pitch_speed_for_squared_up_mph"] = PITCH_SPEED_FALLBACK_MPH
    bat_speed = pd.to_numeric(out["bat_speed_mph_contact_x"], errors="coerce")
    exit_velo = pd.to_numeric(out["exit_velo_mph_x"], errors="coerce")
    max_possible_ev = 1.23 * bat_speed + 0.23 * out["pitch_speed_for_squared_up_mph"]
    out["max_possible_exit_velo_mph_proxy"] = max_possible_ev
    out["squared_up_pct"] = (exit_velo / max_possible_ev * 100.0).clip(lower=0, upper=100)
    out["squared_up_80plus"] = out["squared_up_pct"] >= 80.0
    out["squared_up_90plus"] = out["squared_up_pct"] >= 90.0
    return out


def calculate_swing_lengths(landmarks: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sid, group in landmarks.groupby(landmarks["session_swing"].astype(str), sort=False):
        rows.append(calculate_one_swing_length(str(sid), group))
    return pd.DataFrame(rows)


def calculate_one_swing_length(sid: str, group: pd.DataFrame) -> dict[str, object]:
    g = numeric_frame(group).sort_values("time")
    cols = ["sweet_spot_x", "sweet_spot_y", "sweet_spot_z", "blast_hand_x", "blast_hand_y", "blast_hand_z"]
    row: dict[str, object] = {"session_swing": sid}
    if not set(cols).issubset(g.columns):
        row["swing_length_qc"] = "missing_barrel_or_hand_landmarks"
        return row

    contact = first_numeric(g["contact_time"])
    if not np.isfinite(contact):
        row["swing_length_qc"] = "missing_contact"
        return row

    mask = (g["time"] >= contact - PRIMARY_CONFIG.search_back_s) & (g["time"] <= contact)
    t = g.loc[mask, "time"].to_numpy(float)
    barrel = g.loc[mask, ["sweet_spot_x", "sweet_spot_y", "sweet_spot_z"]].to_numpy(float)
    handle = g.loc[mask, ["blast_hand_x", "blast_hand_y", "blast_hand_z"]].to_numpy(float)
    valid = np.isfinite(t) & np.isfinite(barrel).all(axis=1) & np.isfinite(handle).all(axis=1)
    if valid.sum() < 12:
        row["swing_length_qc"] = "not_enough_valid_frames"
        return row

    dt = median_dt(t[valid])
    if not np.isfinite(dt) or dt <= 0:
        row["swing_length_qc"] = "bad_time_step"
        return row

    barrel[valid] = smooth_positions(barrel[valid], dt, PRIMARY_CONFIG.smooth_ms)
    handle[valid] = smooth_positions(handle[valid], dt, PRIMARY_CONFIG.smooth_ms)
    bat_vector = barrel - handle
    d_vector = component_derivative(t, bat_vector)
    omega_rad_s = np.linalg.norm(np.cross(bat_vector, d_vector), axis=1) / np.maximum(
        np.sum(bat_vector * bat_vector, axis=1), 1e-9
    )
    omega_deg_s = omega_rad_s * 180.0 / np.pi
    omega_deg_s[~valid] = np.nan

    contact_limit = contact - PRIMARY_CONFIG.min_precontact_ms / 1000.0
    eligible = np.where(valid & (t <= contact_limit))[0]
    if len(eligible) < 8:
        eligible = np.where(valid & (t <= contact))[0]
    if len(eligible) < 8:
        row["swing_length_qc"] = "not_enough_precontact_frames"
        return row

    peak_i = int(eligible[np.nanargmax(omega_deg_s[eligible])])
    start_i = latest_path_turn_before_peak(t, barrel, peak_i, valid)
    if start_i is None:
        row["swing_length_qc"] = "no_barrel_inflection_before_peak_omega"
        row["barrel_angular_velocity_peak_ms_before_contact"] = (contact - t[peak_i]) * 1000.0
        row["barrel_angular_velocity_peak_deg_s"] = omega_deg_s[peak_i]
        return row

    contact_i = int(np.nanargmin(np.abs(t - contact)))
    lo, hi = sorted([start_i, contact_i])
    segment = barrel[lo : hi + 1]
    length_m = float(np.nansum(np.linalg.norm(np.diff(segment, axis=0), axis=1)))
    row.update(
        {
            "swing_length_from_barrel_inflection_ft": length_m * M_TO_FT,
            "swing_length_from_barrel_inflection_in": length_m * M_TO_FT * 12.0,
            "swing_length_start_time": t[start_i],
            "swing_length_start_ms_before_contact": (contact - t[start_i]) * 1000.0,
            "barrel_angular_velocity_peak_time": t[peak_i],
            "barrel_angular_velocity_peak_ms_before_contact": (contact - t[peak_i]) * 1000.0,
            "barrel_angular_velocity_peak_deg_s": omega_deg_s[peak_i],
            "swing_length_qc": "ok",
        }
    )
    return row


def latest_path_turn_before_peak(
    time: np.ndarray,
    xyz: np.ndarray,
    peak_i: int,
    valid: np.ndarray,
) -> int | None:
    dt = median_dt(time[valid])
    if not np.isfinite(dt) or dt <= 0:
        return None
    turn_step = max(3, int(round(0.017 / dt)))
    local_gap = max(3, int(round(0.025 / dt)))
    if peak_i <= turn_step + 3:
        return None

    distances = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(xyz, axis=0), axis=1))]
    total_path = distances[min(max(peak_i, 1), len(distances) - 1)]
    if not np.isfinite(total_path) or total_path <= 0:
        return None

    min_leg_distance = 0.003 * total_path
    turn_score = np.full(len(time), np.nan)
    turn_angle = np.full(len(time), np.nan)
    local_motion = np.full(len(time), np.nan)
    end = min(peak_i, len(time) - turn_step - 2)
    for i in range(turn_step, end + 1):
        if not valid[i - turn_step] or not valid[i] or not valid[i + turn_step]:
            continue
        before = xyz[i] - xyz[i - turn_step]
        after = xyz[i + turn_step] - xyz[i]
        before_len = float(np.linalg.norm(before))
        after_len = float(np.linalg.norm(after))
        if before_len <= min_leg_distance or after_len <= min_leg_distance:
            continue
        cos_angle = float(np.dot(before, after) / (before_len * after_len))
        angle = math.acos(max(-1.0, min(1.0, cos_angle)))
        motion = (before_len + after_len) / total_path
        turn_angle[i] = angle
        local_motion[i] = motion
        turn_score[i] = angle * min(1.0, motion / 0.02)

    local = []
    for i in range(turn_step + 1, end):
        if not np.isfinite(turn_score[i]):
            continue
        if turn_score[i] < np.nan_to_num(turn_score[i - 1], nan=-1.0):
            continue
        if turn_score[i] < np.nan_to_num(turn_score[i + 1], nan=-1.0):
            continue
        if local and i - local[-1] < local_gap:
            if turn_score[i] > turn_score[local[-1]]:
                local[-1] = i
        else:
            local.append(i)

    candidates = [
        i
        for i in local
        if math.degrees(turn_angle[i]) >= 10.0 and local_motion[i] >= 0.01
    ]
    return int(candidates[-1]) if candidates else None


def component_derivative(time: np.ndarray, values: np.ndarray) -> np.ndarray:
    out = np.full_like(values, np.nan, dtype=float)
    valid = np.isfinite(time) & np.isfinite(values).all(axis=1)
    if valid.sum() < 3:
        return out
    for axis in range(values.shape[1]):
        out[valid, axis] = np.gradient(values[valid, axis], time[valid])
    return out


def numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col != "session_swing":
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def fit_regression(data: pd.DataFrame, y: str, x: str, label: str) -> dict[str, object]:
    cols = [y, x, "user"]
    d = data.loc[data.get("model_ready_primary", True), cols].dropna().copy()
    if len(d) < 10:
        return {"model": label, "n": len(d), "status": "not_enough_rows"}
    model = smf.ols(f"{y} ~ {x}", data=d).fit(cov_type="HC3")
    clustered = None
    if d["user"].nunique() > 1:
        try:
            clustered = smf.ols(f"{y} ~ {x}", data=d).fit(cov_type="cluster", cov_kwds={"groups": d["user"]})
        except Exception:
            clustered = None
    slope = model.params.get(x, np.nan)
    p_value = model.pvalues.get(x, np.nan)
    cluster_p = clustered.pvalues.get(x, np.nan) if clustered is not None else np.nan
    return {
        "model": label,
        "outcome": y,
        "predictor": x,
        "n": len(d),
        "users": d["user"].nunique(),
        "slope": slope,
        "intercept": model.params.get("Intercept", np.nan),
        "r_squared": model.rsquared,
        "p_value_hc3": p_value,
        "p_value_clustered_by_user": cluster_p,
        "status": "ok",
    }


def fit_logistic(data: pd.DataFrame, y: str, x: str, label: str) -> dict[str, object]:
    cols = [y, x, "user"]
    d = data.loc[data.get("model_ready_primary", True), cols].dropna().copy()
    if len(d) < 20 or d[y].nunique() < 2:
        return {"model": label, "n": len(d), "status": "not_enough_rows_or_classes"}
    d[y] = d[y].astype(int)
    model = smf.logit(f"{y} ~ {x}", data=d).fit(disp=False)
    coef = model.params.get(x, np.nan)
    return {
        "model": label,
        "outcome": y,
        "predictor": x,
        "n": len(d),
        "users": d["user"].nunique(),
        "slope": coef,
        "odds_ratio_per_10ms": math.exp(coef * 10.0) if np.isfinite(coef) else np.nan,
        "intercept": model.params.get("Intercept", np.nan),
        "pseudo_r_squared": model.prsquared,
        "p_value": model.pvalues.get(x, np.nan),
        "status": "ok",
    }


def make_order_distribution(data: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    d = data.loc[data.get("model_ready_primary", True)].copy()
    rows = []
    for order, g in d.groupby("onset_order", dropna=False):
        rows.append(
            {
                "onset_order": order,
                "swings": len(g),
                "users": g["user"].nunique(),
                "pct_swings": len(g) / len(d) * 100.0 if len(d) else np.nan,
                "mean_bat_speed_mph_max": g["bat_speed_mph_max_x"].mean(),
                "median_bat_speed_mph_max": g["bat_speed_mph_max_x"].median(),
                "mean_initiation_spread_ms": g["initiation_spread_ms"].mean(),
                "mean_squared_up_pct": g["squared_up_pct"].mean(),
                "squared_up_90plus_rate": g["squared_up_90plus"].mean(),
                "mean_onset_order_score": g["onset_order_score"].mean(),
            }
        )
    return pd.DataFrame(rows).sort_values(["swings", "onset_order"], ascending=[False, True])


def make_missing_key_point_table(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in data.iterrows():
        missing = [segment for segment in SEGMENTS if pd.isna(row.get(f"{segment}_onset_time"))]
        if not missing:
            continue
        rows.append(
            {
                "session_swing": row.get("session_swing"),
                "user": row.get("user"),
                "session": row.get("session"),
                "hitter_side": row.get("hitter_side"),
                "missing_key_points": ",".join(missing),
                "onset_qc": row.get("onset_qc"),
                "detected_segment_count": row.get("detected_segment_count"),
                "initiation_spread_ms": row.get("initiation_spread_ms"),
                "bat_speed_mph_max_x": row.get("bat_speed_mph_max_x"),
                "pelvis_onset_method": row.get("pelvis_onset_method"),
                "torso_onset_method": row.get("torso_onset_method"),
                "lead_arm_onset_method": row.get("lead_arm_onset_method"),
                "lead_hand_onset_method": row.get("lead_hand_onset_method"),
            }
        )
    cols = [
        "session_swing",
        "user",
        "session",
        "hitter_side",
        "missing_key_points",
        "onset_qc",
        "detected_segment_count",
        "initiation_spread_ms",
        "bat_speed_mph_max_x",
        "pelvis_onset_method",
        "torso_onset_method",
        "lead_arm_onset_method",
        "lead_hand_onset_method",
    ]
    return pd.DataFrame(rows, columns=cols)


def regression_line(ax, x: pd.Series, y: pd.Series, color: str = "#111827") -> None:
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(d) < 2:
        return
    slope, intercept = np.polyfit(d["x"], d["y"], 1)
    xs = np.linspace(d["x"].min(), d["x"].max(), 100)
    ax.plot(xs, slope * xs + intercept, color=color, linewidth=2.4)


def plot_initiation_spread_distribution(data: pd.DataFrame, fig_dir: Path) -> None:
    d = data.dropna(subset=["initiation_spread_ms"]).copy()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    axes[0].hist(d["initiation_spread_ms"], bins=35, color="#2563eb", alpha=0.78, edgecolor="white")
    axes[0].axvline(d["initiation_spread_ms"].median(), color="#111827", linewidth=2, label="median")
    axes[0].axvline(d["initiation_spread_ms"].mean(), color="#dc2626", linewidth=2, linestyle="--", label="mean")
    axes[0].set_xlabel("Initiation spread (ms)")
    axes[0].set_ylabel("Swings")
    axes[0].set_title("Initiation Spread Distribution")
    axes[0].legend(fontsize=8)
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].boxplot(d["initiation_spread_ms"], vert=False, tick_labels=["All swings"], showfliers=True)
    axes[1].set_xlabel("Initiation spread (ms)")
    axes[1].set_title("Initiation Spread Boxplot")
    axes[1].grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "initiation_spread_distribution.png", dpi=170)
    plt.close(fig)


def plot_onset_timing_distributions(data: pd.DataFrame, fig_dir: Path) -> None:
    rows = []
    for segment in SEGMENTS:
        col = f"{segment}_to_contact_ms"
        if col not in data:
            continue
        for value in pd.to_numeric(data[col], errors="coerce").dropna():
            rows.append({"segment": SEGMENT_LABELS[segment], "ms_before_contact": value})
    d = pd.DataFrame(rows)
    if d.empty:
        return

    labels = [SEGMENT_LABELS[segment] for segment in SEGMENTS]
    groups = [d.loc[d["segment"].eq(label), "ms_before_contact"].to_numpy() for label in labels]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    axes[0].boxplot(groups, tick_labels=labels, showfliers=False)
    axes[0].set_ylabel("Onset time (ms before contact)")
    axes[0].set_title("Primary Onset Timing Distributions")
    axes[0].grid(axis="y", alpha=0.25)

    colors = {"Pelvis": "#8e44ad", "Torso": "#2980b9", "Lead Hand": "#0984e3"}
    for label in labels:
        vals = d.loc[d["segment"].eq(label), "ms_before_contact"]
        axes[1].hist(vals, bins=32, alpha=0.42, label=label, color=colors.get(label))
    axes[1].set_xlabel("Onset time (ms before contact)")
    axes[1].set_ylabel("Swings")
    axes[1].set_title("Primary Onset Timing Histograms")
    axes[1].legend(fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "primary_onset_timing_distributions.png", dpi=170)
    plt.close(fig)


def plot_initiation_spread_by_missing_pattern(data: pd.DataFrame, fig_dir: Path) -> None:
    d = data.dropna(subset=["initiation_spread_ms"]).copy()
    patterns = []
    for _, row in d.iterrows():
        missing = [SEGMENT_LABELS[segment] for segment in SEGMENTS if pd.isna(row.get(f"{segment}_onset_time"))]
        patterns.append("None missing" if not missing else "Missing " + ", ".join(missing))
    d["missing_pattern"] = patterns
    order = d.groupby("missing_pattern")["initiation_spread_ms"].median().sort_values(ascending=False).index.tolist()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    groups = [d.loc[d["missing_pattern"].eq(pattern), "initiation_spread_ms"].to_numpy() for pattern in order]
    axes[0].boxplot(groups, tick_labels=order, showfliers=True)
    axes[0].set_ylabel("Initiation spread (ms)")
    axes[0].set_title("Initiation Spread by Missing-Onset Pattern")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].grid(axis="y", alpha=0.25)

    counts = d["detected_segment_count"].value_counts().sort_index()
    axes[1].bar([str(int(k)) for k in counts.index], counts.values, color="#7c3aed", alpha=0.82)
    axes[1].set_xlabel("Detected segment count")
    axes[1].set_ylabel("Swings")
    axes[1].set_title("How Many Key Onsets Were Detected?")
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "initiation_spread_by_missing_pattern.png", dpi=170)
    plt.close(fig)


def plot_bat_speed_vs_spread(data: pd.DataFrame, fig_dir: Path) -> None:
    d = data.dropna(subset=["initiation_spread_ms", "bat_speed_mph_max_x"])
    fig, ax = plt.subplots(figsize=(8.5, 6))
    ax.scatter(d["initiation_spread_ms"], d["bat_speed_mph_max_x"], s=28, alpha=0.58, color="#2563eb")
    regression_line(ax, d["initiation_spread_ms"], d["bat_speed_mph_max_x"])
    ax.set_xlabel("Initiation spread (ms)")
    ax.set_ylabel("Max bat speed (mph)")
    ax.set_title("Max Bat Speed vs Initiation Spread")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "bat_speed_vs_initiation_spread.png", dpi=170)
    plt.close(fig)


def plot_swing_length_vs_spread(data: pd.DataFrame, fig_dir: Path) -> None:
    d = data.dropna(subset=["initiation_spread_ms", "swing_length_from_barrel_inflection_ft"])
    fig, ax = plt.subplots(figsize=(8.5, 6))
    ax.scatter(
        d["initiation_spread_ms"],
        d["swing_length_from_barrel_inflection_ft"],
        s=28,
        alpha=0.58,
        color="#16a34a",
    )
    regression_line(ax, d["initiation_spread_ms"], d["swing_length_from_barrel_inflection_ft"])
    ax.set_xlabel("Initiation spread (ms)")
    ax.set_ylabel("Swing length from barrel inflection (ft)")
    ax.set_title("Swing Length vs Initiation Spread")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "swing_length_vs_initiation_spread.png", dpi=170)
    plt.close(fig)


def plot_onset_order_distribution(order_dist: pd.DataFrame, fig_dir: Path) -> None:
    top = order_dist.head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(top["onset_order"], top["swings"], color="#7c3aed", alpha=0.85)
    ax.set_xlabel("Swings")
    ax.set_title("Most Common Segment Onset Orders")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "onset_order_distribution.png", dpi=170)
    plt.close(fig)


def plot_bat_speed_by_onset_order(data: pd.DataFrame, order_dist: pd.DataFrame, fig_dir: Path) -> None:
    top_orders = order_dist.head(8)["onset_order"].tolist()
    d = data[data["onset_order"].isin(top_orders)].dropna(subset=["bat_speed_mph_max_x"])
    groups = [d.loc[d["onset_order"].eq(order), "bat_speed_mph_max_x"].to_numpy() for order in top_orders]
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.boxplot(groups, tick_labels=top_orders, showfliers=False)
    ax.set_ylabel("Max bat speed (mph)")
    ax.set_title("Bat Speed by Common Onset Order")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "bat_speed_by_onset_order.png", dpi=170)
    plt.close(fig)


def plot_squared_up_vs_spread(data: pd.DataFrame, fig_dir: Path) -> None:
    d = data.dropna(subset=["initiation_spread_ms", "squared_up_pct"])
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    colors = np.where(d["squared_up_90plus"], "#dc2626", "#64748b")
    axes[0].scatter(d["initiation_spread_ms"], d["squared_up_pct"], s=30, alpha=0.62, color=colors)
    regression_line(axes[0], d["initiation_spread_ms"], d["squared_up_pct"])
    axes[0].axhline(90, color="#dc2626", linestyle="--", linewidth=1.5, label="90% threshold")
    axes[0].axhline(80, color="#f59e0b", linestyle=":", linewidth=1.5, label="MLB squared-up threshold")
    axes[0].set_xlabel("Initiation spread (ms)")
    axes[0].set_ylabel("Squared-up percentage")
    axes[0].set_title("Squared-Up % vs Initiation Spread")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.25)

    bins = pd.qcut(d["initiation_spread_ms"], q=4, duplicates="drop")
    rate = d.groupby(bins, observed=False)["squared_up_90plus"].mean() * 100.0
    labels = [f"{interval.left:.0f}-{interval.right:.0f}" for interval in rate.index]
    axes[1].bar(labels, rate.values, color="#dc2626", alpha=0.78)
    axes[1].set_xlabel("Initiation spread quartile (ms)")
    axes[1].set_ylabel("% swings squared up >90%")
    axes[1].set_title("Strict Squared-Up Rate by Initiation Spread")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "squared_up_vs_initiation_spread.png", dpi=170)
    plt.close(fig)


def write_report(
    data: pd.DataFrame,
    regressions: pd.DataFrame,
    order_dist: pd.DataFrame,
    missing_key_points: pd.DataFrame,
    out_dir: Path,
    fig_dir: Path,
) -> Path:
    usable = data.loc[data.get("model_ready_primary", True)]
    swing_ok = data["swing_length_qc"].eq("ok").sum() if "swing_length_qc" in data else 0
    spread_desc = data["initiation_spread_ms"].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(2)
    missing_summary = (
        missing_key_points["missing_key_points"].value_counts().rename_axis("missing_key_points").reset_index(name="swings")
        if len(missing_key_points)
        else pd.DataFrame(columns=["missing_key_points", "swings"])
    )
    lines = [
        "# Initiation Spread Analysis",
        "",
        "This report uses the current piecewise-gated peak signed-angular-acceleration onset outputs. Primary initiation calculations use pelvis, torso, and lead hand; lead arm is still retained in the dataset as a reference onset.",
        "",
        "## Inputs",
        "",
        f"- Swings in model dataset: {len(data)}",
        f"- Model-ready swings: {len(usable)}",
        f"- Swings with calculated barrel-inflection swing length: {int(swing_ok)}",
        "- Squared-up percentage proxy: `exit_velo_mph_x / (1.23 * bat_speed_mph_contact_x + 0.23 * pitch_speed_mph) * 100`.",
        f"- Pitch speed is fixed at {PITCH_SPEED_FALLBACK_MPH:.1f} mph for every swing because the machine setup was constant and `hittrax_pitch` can be noisy/missing.",
        "- MLB's Statcast glossary says 80% or higher is considered squared up; this report also includes your stricter `>90%` flag.",
        "- Statcast describes swing length as total bat-head distance in x/y/z space to impact. This report uses the same distance idea, but starts at the latest selected barrel path turn before peak derived barrel angular velocity.",
        "- Sources: https://www.mlb.com/glossary/statcast/squared-up and https://baseballsavant.mlb.com/leaderboard/bat-tracking",
        "",
        "## Initiation Spread Distribution",
        "",
        spread_desc.to_frame("initiation_spread_ms").to_markdown(),
        "",
        "## Missing Key-Point Onsets",
        "",
        f"- Swings missing at least one key onset: {len(missing_key_points)}",
        "",
        missing_summary.to_markdown(index=False),
        "",
        missing_key_points.head(50).round(3).to_markdown(index=False),
        "",
        "## Regression Summary",
        "",
        regressions.round(4).to_markdown(index=False),
        "",
        "## Common Onset Orders",
        "",
        order_dist.head(15).round(3).to_markdown(index=False),
        "",
        "## Figures",
        "",
    ]
    core_figures = [
        "primary_onset_timing_distributions.png",
        "initiation_spread_distribution.png",
        "initiation_spread_by_missing_pattern.png",
        "bat_speed_vs_initiation_spread.png",
        "swing_length_vs_initiation_spread.png",
        "onset_order_distribution.png",
        "bat_speed_by_onset_order.png",
        "squared_up_vs_initiation_spread.png",
    ]
    for name in core_figures:
        path = fig_dir / name
        if not path.exists():
            continue
        rel = path.relative_to(out_dir)
        lines.append(f"![{path.stem}]({rel.as_posix()})")
        lines.append("")
    path = out_dir / "initiation_analysis_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    write_html_report(path, out_dir / "initiation_analysis_report.html")
    return path


def write_html_report(source: Path, target: Path) -> None:
    import markdown

    text = source.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["extra", "tables", "fenced_code"], output_format="html5")
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Initiation Spread Analysis</title>
  <style>
    body {{ margin: 0; background: #f7f9fb; color: #1f2933; font: 16px/1.55 Arial, sans-serif; }}
    main {{ width: min(1200px, calc(100% - 40px)); margin: 32px auto 56px; padding: 34px 40px; background: white; border: 1px solid #d9e2ec; border-radius: 8px; }}
    h1, h2 {{ line-height: 1.2; }}
    h2 {{ margin-top: 34px; padding-bottom: 8px; border-bottom: 1px solid #d9e2ec; }}
    table {{ display: block; width: 100%; overflow-x: auto; border-collapse: collapse; margin: 16px 0 24px; font-size: 14px; }}
    th, td {{ padding: 8px 10px; border: 1px solid #d9e2ec; vertical-align: top; }}
    th {{ background: #eef2f7; text-align: left; }}
    img {{ display: block; max-width: 100%; margin: 18px 0 30px; border: 1px solid #d9e2ec; border-radius: 8px; }}
    code {{ background: #eef2f7; padding: 2px 5px; border-radius: 4px; }}
  </style>
</head>
<body><main>{body}</main></body>
</html>
"""
    target.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
