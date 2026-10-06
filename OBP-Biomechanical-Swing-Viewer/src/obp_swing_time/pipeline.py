from __future__ import annotations

import argparse
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter
import statsmodels.formula.api as smf


MPS_TO_MPH = 2.2369362921
M_TO_IN = 39.3700787402
LBS_TO_NEWTONS = 4.4482216153
FP_EVENT_SUSTAIN_MS = 25.0
FP_EVENT_STOP_BEFORE_CONTACT_MS = 70.0
FORCE_CLIMB_SMOOTH_MS = 15.0
FORCE_CLIMB_LOCAL_MIN_PROMINENCE_PCT_BW = 0.0
FORCE_CLIMB_BASELINE_MARGIN_PCT_BW = 5.0
FORCE_CLIMB_ZERO_FORCE_PCT_BW = 5.0
FORCE_CLIMB_ZERO_FORCE_MIN_MS = 200.0
FORCE_QC_EXCLUDE_SWINGS = {"287_4", "268_8", "378_8"}
FORCE_PEAK_USE_PRECONTACT_SWINGS = {"398_6"}


ANGULAR_ONSET_COLS = {
    "pelvis": [
        "pelvis_angular_velocity_x",
        "pelvis_angular_velocity_y",
        "pelvis_angular_velocity_z",
    ],
    "torso": [
        "torso_angular_velocity_x",
        "torso_angular_velocity_y",
        "torso_angular_velocity_z",
    ],
    "lead_arm": [
        "lead_elbow_angular_velocity_x",
        "lead_elbow_angular_velocity_y",
        "lead_elbow_angular_velocity_z",
    ],
    "lead_hand": [
        "lead_hand_global_angular_velocity_x",
        "lead_hand_global_angular_velocity_y",
        "lead_hand_global_angular_velocity_z",
    ],
}

INITIATION_SEGMENTS = ["pelvis", "torso", "lead_hand"]
MANUAL_QC_EXCLUSIONS = {}
LEAD_HAND_BURST_WINDOW_MS = (-200.0, -100.0)
LEAD_HAND_BURST_THRESHOLD_PCT = 0.15
LEAD_HAND_LOAD_BACK_MIN_DISPLACEMENT_M = 0.02
LEAD_HAND_FORWARD_VELOCITY_THRESHOLD_MPS = 0.20
LEAD_HAND_ACCEL_JUMP_THRESHOLD_PCT = 0.15
LEAD_HAND_BARREL_REVERSAL_SEARCH_WINDOW_MS = (-300.0, -60.0)
LEAD_HAND_BARREL_REVERSAL_REFERENCE_WINDOW_MS = (-125.0, -50.0)
LEAD_HAND_BARREL_REVERSAL_SUSTAIN_MS = 25.0


@dataclass(frozen=True)
class OnsetConfig:
    # threshold_pct and sustained_ms are retained only for the legacy fallback detector.
    threshold_pct: float = 0.10
    sustained_ms: float = 15.0
    search_back_s: float = 0.50
    smooth_ms: float = 17.0
    inflection_prominence_pct: float = 0.45
    min_precontact_ms: float = 25.0
    inflection_velocity_gate_pct: float = 0.50
    path_turn_velocity_gate_pct: float = 0.15
    path_turn_min_angle_deg: float = 10.0
    burst_peak_threshold_pct: float = 0.25
    burst_reference_ms_before_contact: float = 191.7

    @property
    def label(self) -> str:
        window = int(round(self.search_back_s * 1000))
        smooth = int(round(self.smooth_ms))
        prominence = int(round(self.inflection_prominence_pct * 100))
        gate = int(round(self.inflection_velocity_gate_pct * 100))
        return f"inflect_win{window}ms_smooth{smooth}ms_prom{prominence}_vel{gate}"


PRIMARY_CONFIG = OnsetConfig()
SENSITIVITY_CONFIGS = [
    OnsetConfig(search_back_s=0.45, smooth_ms=13.0, inflection_prominence_pct=0.40),
    OnsetConfig(search_back_s=0.50, smooth_ms=17.0, inflection_prominence_pct=0.45),
    OnsetConfig(search_back_s=0.60, smooth_ms=21.0, inflection_prominence_pct=0.50),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze OBP hitting swing time.")
    parser.add_argument("--data-root", default=r"E:\Baseball\Data\OBP")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--max-swings", type=int, default=None)
    args = parser.parse_args(argv)

    data_root = Path(args.data_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(parents=True, exist_ok=True)

    paths = expected_paths(data_root)
    validate_paths(paths)

    print("Loading metadata and summary tables...")
    metadata = read_csv(paths["metadata"])
    poi = read_csv(paths["poi"])
    hittrax = read_csv(paths["hittrax"])

    selected_swings = select_swings(metadata["session_swing"], args.max_swings)

    print("Loading full-signal tables from zip archives...")
    landmarks = read_zipped_csv(paths["landmarks"], selected_swings)
    joint_velos = read_zipped_csv(paths["joint_velos"], selected_swings)
    force = read_zipped_csv(paths["force_plate"], selected_swings, required=False)
    fp_events = calculate_latest_force_plate_events(force, metadata, landmarks)
    landmarks = apply_force_plate_event_updates(landmarks, fp_events)
    joint_velos = apply_force_plate_event_updates(joint_velos, fp_events)
    force = apply_force_plate_event_updates(force, fp_events) if len(force) else force

    print("Building data dictionary and QC manifest...")
    data_dictionary = build_data_dictionary(paths)
    manifest = build_manifest(metadata, poi, hittrax, landmarks, force)

    print("Detecting segment onsets and composite swing time...")
    onset_metrics, sensitivity = calculate_all_onsets(
        landmarks, joint_velos, metadata, PRIMARY_CONFIG, SENSITIVITY_CONFIGS
    )

    print("Calculating barrel/path metrics...")
    barrel_metrics = calculate_barrel_metrics(landmarks, onset_metrics)

    print("Calculating peak-velocity sequencing...")
    sequence_metrics = calculate_sequence_metrics(joint_velos)

    print("Joining model dataset...")
    model_dataset = build_model_dataset(
        metadata, poi, hittrax, manifest, barrel_metrics, onset_metrics, sequence_metrics
    )

    print("Writing outputs...")
    write_table(data_dictionary, output_dir / "data_dictionary.csv")
    write_table(manifest, output_dir / "swing_manifest.csv")
    write_table(onset_metrics, output_dir / "onset_metrics.csv")
    write_table(sensitivity, output_dir / "sensitivity_onsets.csv")
    write_table(barrel_metrics, output_dir / "barrel_metrics.csv")
    write_table(sequence_metrics, output_dir / "sequence_metrics.csv")
    write_table(model_dataset, output_dir / "model_dataset.csv")

    qc_summary = build_qc_summary(manifest, onset_metrics, model_dataset)
    write_table(qc_summary, output_dir / "qc_summary.csv", parquet=False)

    print("Creating figures and model summaries...")
    figure_paths = make_figures(model_dataset, output_dir / "figures")
    model_summaries = fit_models(model_dataset)
    write_report(
        output_dir / "analysis_report.md",
        data_root,
        manifest,
        onset_metrics,
        barrel_metrics,
        model_dataset,
        qc_summary,
        model_summaries,
        figure_paths,
    )

    print(f"Done. Report: {output_dir / 'analysis_report.md'}")
    return 0


def expected_paths(data_root: Path) -> dict[str, Path]:
    return {
        "metadata": data_root / "Baseball Hitting" / "2-12-26.OBP.csv",
        "poi": data_root / "Baseball Hitting" / "poi_metrics.csv",
        "hittrax": data_root / "Baseball Hitting" / "hittrax.csv",
        "landmarks": data_root / "3D" / "landmarks.zip",
        "joint_velos": data_root / "3D" / "joint_velos.zip",
        "force_plate": data_root / "3D" / "force_plate.zip",
    }


def validate_paths(paths: dict[str, Path]) -> None:
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing expected OBP files:\n" + "\n".join(missing))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def select_swings(ids: Iterable[str], max_swings: int | None) -> set[str] | None:
    if max_swings is None:
        return None
    return set(pd.Series(list(ids)).dropna().astype(str).head(max_swings))


def read_zipped_csv(
    zip_path: Path, selected_swings: set[str] | None, required: bool = True
) -> pd.DataFrame:
    if not zip_path.exists():
        if required:
            raise FileNotFoundError(zip_path)
        return pd.DataFrame()

    with zipfile.ZipFile(zip_path) as zf:
        names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not names:
            raise FileNotFoundError(f"No CSV found inside {zip_path}")
        with zf.open(names[0]) as handle:
            if selected_swings is None:
                return pd.read_csv(handle)
            chunks = []
            for chunk in pd.read_csv(handle, chunksize=100_000):
                chunk["session_swing"] = chunk["session_swing"].astype(str)
                keep = chunk["session_swing"].isin(selected_swings)
                if keep.any():
                    chunks.append(chunk.loc[keep].copy())
            return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def build_data_dictionary(paths: dict[str, Path]) -> pd.DataFrame:
    rows = []
    for name, path in paths.items():
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as zf:
                csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
                with zf.open(csv_name) as handle:
                    sample = pd.read_csv(handle, nrows=50)
        else:
            sample = pd.read_csv(path, nrows=50)
        for col in sample.columns:
            example = sample[col].dropna().astype(str).head(1)
            rows.append(
                {
                    "dataset": name,
                    "column": col,
                    "dtype": str(sample[col].dtype),
                    "example": example.iloc[0] if len(example) else "",
                    "role": infer_column_role(col),
                }
            )
    return pd.DataFrame(rows)


def calculate_lead_force_abs_max(
    time: np.ndarray,
    force_z: np.ndarray,
    body_weight_n: float,
    contact: float,
) -> dict[str, float]:
    result = {
        "lead_force_abs_max_time": np.nan,
        "lead_force_abs_max_n": np.nan,
        "lead_force_abs_max_pct_bw": np.nan,
        "lead_force_signed_at_abs_max_n": np.nan,
        "lead_force_signed_at_abs_max_pct_bw": np.nan,
        "lead_force_min_time": np.nan,
        "lead_force_min_pct_bw": np.nan,
        "lead_force_max_time": np.nan,
        "lead_force_max_pct_bw": np.nan,
        "lead_force_range_pct_bw": np.nan,
        "lead_force_corrected_max_pct_bw": np.nan,
        "lead_force_precontact_abs_max_time": np.nan,
        "lead_force_precontact_abs_max_pct_bw": np.nan,
        "lead_force_precontact_signed_at_abs_max_pct_bw": np.nan,
        "lead_force_precontact_min_time": np.nan,
        "lead_force_precontact_min_pct_bw": np.nan,
        "lead_force_precontact_max_time": np.nan,
        "lead_force_precontact_max_pct_bw": np.nan,
        "lead_force_precontact_range_pct_bw": np.nan,
        "lead_force_precontact_corrected_max_pct_bw": np.nan,
    }
    valid = np.isfinite(time) & np.isfinite(force_z)
    if not valid.any() or not np.isfinite(body_weight_n) or body_weight_n <= 0:
        return result
    time = time[valid]
    force_z = force_z[valid]
    pct = force_z / body_weight_n * 100.0

    abs_idx = int(np.nanargmax(np.abs(force_z)))
    signed_force = float(force_z[abs_idx])
    abs_force = abs(signed_force)
    result["lead_force_abs_max_time"] = float(time[abs_idx])
    result["lead_force_abs_max_n"] = abs_force
    result["lead_force_abs_max_pct_bw"] = float(abs_force / body_weight_n * 100.0)
    result["lead_force_signed_at_abs_max_n"] = signed_force
    result["lead_force_signed_at_abs_max_pct_bw"] = float(signed_force / body_weight_n * 100.0)

    min_idx = int(np.nanargmin(pct))
    max_idx = int(np.nanargmax(pct))
    result["lead_force_min_time"] = float(time[min_idx])
    result["lead_force_min_pct_bw"] = float(pct[min_idx])
    result["lead_force_max_time"] = float(time[max_idx])
    result["lead_force_max_pct_bw"] = float(pct[max_idx])
    result["lead_force_range_pct_bw"] = float(pct[max_idx] - pct[min_idx])
    result["lead_force_corrected_max_pct_bw"] = float(pct[max_idx] - min(pct[min_idx], 0.0))

    if np.isfinite(contact):
        pre = time <= contact
        if pre.any():
            pre_time = time[pre]
            pre_pct = pct[pre]
            pre_abs_idx = int(np.nanargmax(np.abs(pre_pct)))
            pre_min_idx = int(np.nanargmin(pre_pct))
            pre_max_idx = int(np.nanargmax(pre_pct))
            result["lead_force_precontact_abs_max_time"] = float(pre_time[pre_abs_idx])
            result["lead_force_precontact_abs_max_pct_bw"] = float(abs(pre_pct[pre_abs_idx]))
            result["lead_force_precontact_signed_at_abs_max_pct_bw"] = float(pre_pct[pre_abs_idx])
            result["lead_force_precontact_min_time"] = float(pre_time[pre_min_idx])
            result["lead_force_precontact_min_pct_bw"] = float(pre_pct[pre_min_idx])
            result["lead_force_precontact_max_time"] = float(pre_time[pre_max_idx])
            result["lead_force_precontact_max_pct_bw"] = float(pre_pct[pre_max_idx])
            result["lead_force_precontact_range_pct_bw"] = float(pre_pct[pre_max_idx] - pre_pct[pre_min_idx])
            result["lead_force_precontact_corrected_max_pct_bw"] = float(
                pre_pct[pre_max_idx] - min(pre_pct[pre_min_idx], 0.0)
            )
    return result


def infer_column_role(col: str) -> str:
    c = col.lower()
    if c in {"session_swing", "session", "user"}:
        return "identifier"
    if c.endswith("_time") or c == "time":
        return "time/event"
    if "velo" in c or "velocity" in c or "speed" in c:
        return "velocity/speed"
    if "angle" in c or "x_factor" in c:
        return "angle"
    if "force" in c:
        return "force"
    if c.endswith(("_x", "_y", "_z")):
        return "3d_component"
    return "metadata/outcome"



def calculate_latest_force_plate_events(
    force: pd.DataFrame,
    metadata: pd.DataFrame,
    landmarks: pd.DataFrame,
) -> pd.DataFrame:
    if force.empty or "session_swing" not in force or "lead_force_z" not in force:
        return pd.DataFrame()

    meta = metadata.copy()
    meta["session_swing"] = meta["session_swing"].astype(str)
    mass_lbs = pd.to_numeric(meta.get("session_mass_lbs"), errors="coerce")
    mass_by_sid = dict(zip(meta["session_swing"], mass_lbs))

    landmark_contact = {}
    if not landmarks.empty and {"session_swing", "contact_time"}.issubset(landmarks.columns):
        contacts = landmarks[["session_swing", "contact_time"]].drop_duplicates("session_swing").copy()
        contacts["session_swing"] = contacts["session_swing"].astype(str)
        contacts["contact_time"] = pd.to_numeric(contacts["contact_time"], errors="coerce")
        landmark_contact = dict(zip(contacts["session_swing"], contacts["contact_time"]))

    rows = []
    for sid, group in force.groupby(force["session_swing"].astype(str), sort=False):
        g = group.sort_values("time").copy()
        time = pd.to_numeric(g.get("time"), errors="coerce").to_numpy(float)
        lead_force_z = pd.to_numeric(g.get("lead_force_z"), errors="coerce").to_numpy(float)
        contact = first_numeric(g["contact_time"]) if "contact_time" in g else np.nan
        if not np.isfinite(contact):
            contact = float(landmark_contact.get(str(sid), np.nan))
        mass = float(mass_by_sid.get(str(sid), np.nan))
        body_weight_n = mass * LBS_TO_NEWTONS if np.isfinite(mass) and mass > 0 else np.nan

        raw_fp10 = first_numeric(g["fp_10_time"]) if "fp_10_time" in g else np.nan
        raw_fp100 = first_numeric(g["fp_100_time"]) if "fp_100_time" in g else np.nan
        fp10, fp10_source = latest_sustained_force_crossing(time, lead_force_z, contact, body_weight_n, 0.10)
        fp100, fp100_source = latest_sustained_force_crossing(time, lead_force_z, contact, body_weight_n, 1.00)
        climb = detect_force_climb_start(time, lead_force_z, contact, body_weight_n, fp100)
        force_max = calculate_lead_force_abs_max(time, lead_force_z, body_weight_n, contact)
        force_peak_note = "ok"
        if str(sid) in FORCE_PEAK_USE_PRECONTACT_SWINGS:
            pre_time = force_max.get("lead_force_precontact_max_time", np.nan)
            if np.isfinite(pre_time):
                force_max["lead_force_max_time"] = pre_time
                force_max["lead_force_max_pct_bw"] = force_max.get("lead_force_precontact_max_pct_bw", np.nan)
                force_max["lead_force_corrected_max_pct_bw"] = force_max.get(
                    "lead_force_precontact_corrected_max_pct_bw", np.nan
                )
                force_peak_note = "manual_precontact_peak"

        rows.append(
            {
                "session_swing": str(sid),
                "fp_10_time_raw": raw_fp10,
                "fp_100_time_raw": raw_fp100,
                "fp_10_time": fp10,
                "fp_100_time": fp100,
                "fp_10_source": fp10_source,
                "fp_100_source": fp100_source,
                "force_qc_exclude": str(sid) in FORCE_QC_EXCLUDE_SWINGS,
                "force_qc_note": "manual_force_dq" if str(sid) in FORCE_QC_EXCLUDE_SWINGS else "ok",
                "force_peak_note": force_peak_note,
                **climb,
                **force_max,
            }
        )
    return pd.DataFrame(rows)


def detect_force_climb_start(
    time: np.ndarray,
    force_z: np.ndarray,
    contact: float,
    body_weight_n: float,
    fp100_time: float,
) -> dict[str, float | str]:
    result: dict[str, float | str] = {
        "force_climb_start_time": np.nan,
        "force_climb_start_source": "not_detected",
        "force_climb_local_min_count": 0.0,
        "force_climb_start_force_pct_bw": np.nan,
        "force_climb_start_to_fp100_ms": np.nan,
    }
    valid = np.isfinite(time) & np.isfinite(force_z)
    time = time[valid]
    force_z = force_z[valid]
    if (
        len(time) < 8
        or not np.isfinite(contact)
        or not np.isfinite(body_weight_n)
        or body_weight_n <= 0
        or not np.isfinite(fp100_time)
    ):
        result["force_climb_start_source"] = "missing_force_or_fp100"
        return result

    order = np.argsort(time)
    time = time[order]
    force_z = force_z[order]
    search = time < fp100_time
    time = time[search]
    force_z = force_z[search]
    if len(time) < 8:
        result["force_climb_start_source"] = "no_pre_fp100_force"
        return result

    force_pct = force_z / body_weight_n * 100.0
    dt = median_dt(time)
    if not np.isfinite(dt) or dt <= 0:
        dt = 1 / 1000.0
    smooth_n = max(5, int(round((FORCE_CLIMB_SMOOTH_MS / 1000.0) / dt)))
    if smooth_n % 2 == 0:
        smooth_n += 1
    smoothed = (
        pd.Series(force_pct)
        .rolling(window=smooth_n, center=True, min_periods=max(2, smooth_n // 3))
        .mean()
        .to_numpy(float)
    )
    finite = np.isfinite(smoothed)
    idxs = np.where(finite)[0]
    if len(idxs) < 8:
        result["force_climb_start_source"] = "no_smoothed_force"
        return result

    zero_baseline = smoothed <= FORCE_CLIMB_ZERO_FORCE_PCT_BW
    zero_run_start = np.nan
    zero_run_end = np.nan
    zero_runs: list[tuple[float, float]] = []
    run_start: int | None = None
    for idx in idxs:
        if zero_baseline[idx]:
            if run_start is None:
                run_start = int(idx)
        else:
            if run_start is not None and (time[idx - 1] - time[run_start]) * 1000.0 >= FORCE_CLIMB_ZERO_FORCE_MIN_MS:
                zero_runs.append((float(time[run_start]), float(time[idx - 1])))
            run_start = None
    if run_start is not None and (time[idxs[-1]] - time[run_start]) * 1000.0 >= FORCE_CLIMB_ZERO_FORCE_MIN_MS:
        zero_runs.append((float(time[run_start]), float(time[idxs[-1]])))
    if zero_runs:
        zero_run_start, zero_run_end = zero_runs[-1]
    has_zero_baseline_run = (
        np.isfinite(zero_run_start)
        and np.isfinite(zero_run_end)
        and (zero_run_end - zero_run_start) * 1000.0 >= FORCE_CLIMB_ZERO_FORCE_MIN_MS
    )

    # Branch 1: a meaningful valley exists before FP100, so use the last one.
    # If the hitter sat near zero force for 200+ ms, treat tiny valleys as baseline noise.
    local_min_indices: list[int] = []
    local_min_prominences: list[float] = []
    peaks, props = find_peaks(-smoothed[idxs], prominence=FORCE_CLIMB_LOCAL_MIN_PROMINENCE_PCT_BW)
    if len(peaks):
        local_min_indices = idxs[peaks].astype(int).tolist()
        local_min_prominences = [float(x) for x in props.get("prominences", [])]
    if has_zero_baseline_run:
        usable_local_min_indices = [idx for idx in local_min_indices if time[idx] > zero_run_end]
    else:
        usable_local_min_indices = local_min_indices
    result["force_climb_local_min_count"] = float(len(usable_local_min_indices))

    rfd = np.gradient(smoothed, time)
    if usable_local_min_indices:
        valley = int(usable_local_min_indices[-1])
        threshold = float(smoothed[valley] + FORCE_CLIMB_BASELINE_MARGIN_PCT_BW)
        after_valley = idxs[(idxs > valley) & np.isfinite(smoothed[idxs]) & np.isfinite(rfd[idxs])]
        breakout_candidates = after_valley[(smoothed[after_valley] >= threshold) & (rfd[after_valley] > 0)]
        if len(breakout_candidates):
            chosen = int(breakout_candidates[0])
            result["force_climb_start_source"] = (
                "last_local_min_after_zero_baseline_plus5bw_breakout"
                if has_zero_baseline_run
                else "last_local_min_before_fp100_plus5bw_breakout"
            )
        else:
            chosen = valley
            result["force_climb_start_source"] = (
                "last_local_min_after_zero_baseline_no_plus5bw_breakout"
                if has_zero_baseline_run
                else "last_local_min_before_fp100_no_plus5bw_breakout"
            )
    else:
        # Branch 2: no useful valley exists; use the end of the quiet baseline before the steepest rise.
        finite_rfd = idxs[np.isfinite(rfd[idxs]) & np.isfinite(smoothed[idxs])]
        if len(finite_rfd) < 3:
            result["force_climb_start_source"] = "no_rfd_signal"
            return result
        steepest = int(finite_rfd[np.nanargmax(rfd[finite_rfd])])
        before = idxs[idxs <= steepest]
        if len(before) < 3:
            result["force_climb_start_source"] = "no_pre_steepest_baseline"
            return result
        baseline = float(np.nanpercentile(smoothed[before], 10))
        threshold = baseline + FORCE_CLIMB_BASELINE_MARGIN_PCT_BW
        candidates = before[smoothed[before] <= threshold]
        chosen = int(candidates[-1]) if len(candidates) else int(before[np.nanargmin(smoothed[before])])
        result["force_climb_start_source"] = (
            "zero_baseline_breakout_before_fp100" if has_zero_baseline_run else "baseline_breakout_before_fp100"
        )

    climb_time = float(time[chosen])
    result["force_climb_start_time"] = climb_time
    result["force_climb_start_force_pct_bw"] = float(smoothed[chosen])
    result["force_climb_start_to_fp100_ms"] = float((fp100_time - climb_time) * 1000.0)
    return result


def latest_sustained_force_crossing(
    time: np.ndarray,
    force_z: np.ndarray,
    contact: float,
    body_weight_n: float,
    threshold_fraction: float,
) -> tuple[float, str]:
    valid = np.isfinite(time) & np.isfinite(force_z)
    time = time[valid]
    force_z = force_z[valid]
    if len(time) < 3 or not np.isfinite(contact) or not np.isfinite(body_weight_n) or body_weight_n <= 0:
        return np.nan, "missing_force_or_body_weight"

    order = np.argsort(time)
    time = time[order]
    force_z = force_z[order]
    detection_stop = contact - (FP_EVENT_STOP_BEFORE_CONTACT_MS / 1000.0)
    pre = time < detection_stop
    time = time[pre]
    force_z = force_z[pre]
    if len(time) < 3:
        return np.nan, "no_precontact_force"

    threshold = body_weight_n * threshold_fraction
    above = force_z >= threshold
    sustain_s = FP_EVENT_SUSTAIN_MS / 1000.0
    crossings: list[float] = []
    for i in range(1, len(time)):
        if above[i] and not above[i - 1]:
            sustain_end = time[i] + sustain_s
            sustain = (time >= time[i]) & (time <= sustain_end)
            if sustain.any() and np.all(force_z[sustain] >= threshold):
                prev_force = force_z[i - 1]
                curr_force = force_z[i]
                denom = curr_force - prev_force
                if abs(denom) > 1e-9:
                    frac = float(np.clip((threshold - prev_force) / denom, 0.0, 1.0))
                    crossings.append(float(time[i - 1] + frac * (time[i] - time[i - 1])))
                else:
                    crossings.append(float(time[i]))

    if crossings:
        return float(crossings[-1]), "latest_sustained_upward_crossing"
    if above[0]:
        return float(time[0]), "already_above_first_force_frame"
    return np.nan, "not_detected"


def apply_force_plate_event_updates(frame: pd.DataFrame, fp_events: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or fp_events.empty or "session_swing" not in frame:
        return frame
    update_cols = [
        "session_swing",
        "fp_10_time",
        "fp_100_time",
        "fp_10_time_raw",
        "fp_100_time_raw",
        "fp_10_source",
        "fp_100_source",
        "force_climb_start_time",
        "force_climb_start_source",
        "force_climb_local_min_count",
        "force_climb_start_force_pct_bw",
        "force_climb_start_to_fp100_ms",
        "lead_force_abs_max_time",
        "lead_force_abs_max_n",
        "lead_force_abs_max_pct_bw",
        "lead_force_signed_at_abs_max_n",
        "lead_force_signed_at_abs_max_pct_bw",
        "lead_force_min_time",
        "lead_force_min_pct_bw",
        "lead_force_max_time",
        "lead_force_max_pct_bw",
        "lead_force_range_pct_bw",
        "lead_force_corrected_max_pct_bw",
        "lead_force_precontact_abs_max_time",
        "lead_force_precontact_abs_max_pct_bw",
        "lead_force_precontact_signed_at_abs_max_pct_bw",
        "lead_force_precontact_min_time",
        "lead_force_precontact_min_pct_bw",
        "lead_force_precontact_max_time",
        "lead_force_precontact_max_pct_bw",
        "lead_force_precontact_range_pct_bw",
        "lead_force_precontact_corrected_max_pct_bw",
        "force_qc_exclude",
        "force_qc_note",
        "force_peak_note",
    ]
    updates = fp_events[[c for c in update_cols if c in fp_events.columns]].copy()
    updates["session_swing"] = updates["session_swing"].astype(str)
    out = frame.copy()
    out["session_swing"] = out["session_swing"].astype(str)
    out = out.merge(updates, on="session_swing", how="left", suffixes=("", "_latest_fp"))
    for col in ["fp_10_time", "fp_100_time"]:
        latest_col = f"{col}_latest_fp"
        if latest_col in out:
            latest = pd.to_numeric(out[latest_col], errors="coerce")
            if col in out:
                current = pd.to_numeric(out[col], errors="coerce")
                out[col] = latest.where(latest.notna(), current)
            else:
                out[col] = latest
            out = out.drop(columns=[latest_col])
    return out


def build_manifest(
    metadata: pd.DataFrame,
    poi: pd.DataFrame,
    hittrax: pd.DataFrame,
    landmarks: pd.DataFrame,
    force: pd.DataFrame,
) -> pd.DataFrame:
    meta = metadata.copy()
    meta["session_swing"] = meta["session_swing"].astype(str)
    poi_ids = set(poi["session_swing"].astype(str))
    hit_ids = set(hittrax["session_swing"].astype(str))
    force_ids = set(force["session_swing"].astype(str)) if len(force) else set()

    event_cols = ["fp_10_time", "fp_100_time", "contact_time"]
    optional_event_cols = [
        "fp_10_time_raw",
        "fp_100_time_raw",
        "fp_10_source",
        "fp_100_source",
        "force_climb_start_time",
        "force_climb_start_source",
        "force_climb_local_min_count",
        "force_climb_start_force_pct_bw",
        "force_climb_start_to_fp100_ms",
        "lead_force_abs_max_time",
        "lead_force_abs_max_n",
        "lead_force_abs_max_pct_bw",
        "lead_force_signed_at_abs_max_n",
        "lead_force_signed_at_abs_max_pct_bw",
        "lead_force_min_time",
        "lead_force_min_pct_bw",
        "lead_force_max_time",
        "lead_force_max_pct_bw",
        "lead_force_range_pct_bw",
        "lead_force_corrected_max_pct_bw",
        "lead_force_precontact_abs_max_time",
        "lead_force_precontact_abs_max_pct_bw",
        "lead_force_precontact_signed_at_abs_max_pct_bw",
        "lead_force_precontact_min_time",
        "lead_force_precontact_min_pct_bw",
        "lead_force_precontact_max_time",
        "lead_force_precontact_max_pct_bw",
        "lead_force_precontact_range_pct_bw",
        "lead_force_precontact_corrected_max_pct_bw",
        "force_qc_exclude",
        "force_qc_note",
        "force_peak_note",
    ]
    available_event_cols = [*event_cols, *[c for c in optional_event_cols if c in landmarks.columns]]
    events = (
        landmarks[["session_swing", *available_event_cols]]
        .drop_duplicates("session_swing")
        .copy()
    )
    events["session_swing"] = events["session_swing"].astype(str)
    for col in [
        *event_cols,
        "fp_10_time_raw",
        "fp_100_time_raw",
        "force_climb_start_time",
        "force_climb_local_min_count",
        "force_climb_start_force_pct_bw",
        "force_climb_start_to_fp100_ms",
        "lead_force_abs_max_time",
        "lead_force_abs_max_n",
        "lead_force_abs_max_pct_bw",
        "lead_force_signed_at_abs_max_n",
        "lead_force_signed_at_abs_max_pct_bw",
        "lead_force_min_time",
        "lead_force_min_pct_bw",
        "lead_force_max_time",
        "lead_force_max_pct_bw",
        "lead_force_range_pct_bw",
        "lead_force_corrected_max_pct_bw",
        "lead_force_precontact_abs_max_time",
        "lead_force_precontact_abs_max_pct_bw",
        "lead_force_precontact_signed_at_abs_max_pct_bw",
        "lead_force_precontact_min_time",
        "lead_force_precontact_min_pct_bw",
        "lead_force_precontact_max_time",
        "lead_force_precontact_max_pct_bw",
        "lead_force_precontact_range_pct_bw",
        "lead_force_precontact_corrected_max_pct_bw",
    ]:
        if col in events:
            events[col] = pd.to_numeric(events[col], errors="coerce")

    frame_stats = (
        landmarks.groupby("session_swing", as_index=False)
        .agg(first_time=("time", "min"), last_time=("time", "max"), frames=("time", "size"))
    )
    frame_stats["session_swing"] = frame_stats["session_swing"].astype(str)

    out = meta.merge(events, on="session_swing", how="left").merge(
        frame_stats, on="session_swing", how="left"
    )
    out["has_poi"] = out["session_swing"].isin(poi_ids)
    out["has_hittrax"] = out["session_swing"].isin(hit_ids)
    out["has_force"] = out["session_swing"].isin(force_ids)
    out["has_all_events"] = out[event_cols].notna().all(axis=1)
    out["event_order_valid"] = (
        out["has_all_events"]
        & (out["fp_10_time"] <= out["fp_100_time"])
        & (out["fp_100_time"] <= out["contact_time"])
    )
    out["contact_in_window"] = (
        out["contact_time"].notna()
        & (out["first_time"] <= out["contact_time"])
        & (out["contact_time"] <= out["last_time"])
    )
    out["analysis_event_valid"] = out["contact_in_window"] & out["contact_time"].notna()
    out["fp10_to_contact_ms"] = (out["contact_time"] - out["fp_10_time"]) * 1000.0
    out["fp100_to_contact_ms"] = (out["contact_time"] - out["fp_100_time"]) * 1000.0
    out["fp10_to_fp100_ms"] = (out["fp_100_time"] - out["fp_10_time"]) * 1000.0
    out["force_climb_start_to_contact_ms"] = (out["contact_time"] - out["force_climb_start_time"]) * 1000.0
    out["force_climb_start_to_fp100_ms"] = (out["fp_100_time"] - out["force_climb_start_time"]) * 1000.0
    out["lead_force_abs_max_to_contact_ms"] = (out["contact_time"] - out["lead_force_abs_max_time"]) * 1000.0
    out["lead_force_min_to_contact_ms"] = (out["contact_time"] - out["lead_force_min_time"]) * 1000.0
    out["lead_force_max_to_contact_ms"] = (out["contact_time"] - out["lead_force_max_time"]) * 1000.0
    out["lead_force_precontact_abs_max_to_contact_ms"] = (out["contact_time"] - out["lead_force_precontact_abs_max_time"]) * 1000.0
    out["lead_force_precontact_min_to_contact_ms"] = (out["contact_time"] - out["lead_force_precontact_min_time"]) * 1000.0
    out["lead_force_precontact_max_to_contact_ms"] = (out["contact_time"] - out["lead_force_precontact_max_time"]) * 1000.0
    out["recorded_duration_s"] = out["last_time"] - out["first_time"]
    return out


def calculate_barrel_metrics(
    landmarks: pd.DataFrame, onset_metrics: pd.DataFrame | None = None
) -> pd.DataFrame:
    rows = []
    needed = ["sweet_spot_x", "sweet_spot_y", "sweet_spot_z", "thorax_ap_x", "thorax_ap_y", "thorax_ap_z"]
    barrel_onsets = {}
    if onset_metrics is not None and "barrel_onset_time" in onset_metrics:
        barrel_onsets = (
            onset_metrics.set_index("session_swing")["barrel_onset_time"]
            .apply(pd.to_numeric, errors="coerce")
            .to_dict()
        )
    for sid, group in landmarks.groupby("session_swing", sort=False):
        g = group.sort_values("time")
        contact = first_numeric(g["contact_time"])
        if not np.isfinite(contact) or any(col not in g for col in needed):
            rows.append({"session_swing": sid, "barrel_qc": "missing_contact_or_columns"})
            continue

        t = g["time"].to_numpy(float)
        xyz = g[["sweet_spot_x", "sweet_spot_y", "sweet_spot_z"]].to_numpy(float)
        valid = np.isfinite(t) & np.isfinite(xyz).all(axis=1)
        t = t[valid]
        xyz = xyz[valid]
        if len(t) < 5:
            rows.append({"session_swing": sid, "barrel_qc": "too_few_frames"})
            continue

        contact_i = nearest_index(t, contact)
        start_i = max(0, np.searchsorted(t, contact - 0.50, side="left"))
        final150_i = max(0, np.searchsorted(t, contact - 0.150, side="left"))
        barrel_onset = barrel_onsets.get(str(sid), np.nan)
        onset_i = (
            max(0, np.searchsorted(t, barrel_onset, side="left"))
            if np.isfinite(barrel_onset)
            else start_i
        )
        speed_mps = speed_from_positions(t, xyz)
        peak_i = int(np.nanargmax(speed_mps[start_i : contact_i + 1]) + start_i)

        full_path_m = path_length(xyz[start_i : contact_i + 1])
        onset_path_m = path_length(xyz[onset_i : contact_i + 1])
        final150_path_m = path_length(xyz[final150_i : contact_i + 1])
        contact_pos = xyz[contact_i]
        thorax = g[["thorax_ap_x", "thorax_ap_y", "thorax_ap_z"]].to_numpy(float)[valid]
        thorax_contact = thorax[contact_i] if len(thorax) > contact_i else np.array([np.nan] * 3)

        rows.append(
            {
                "session_swing": sid,
                "barrel_qc": "ok",
                "barrel_path_500ms_in": full_path_m * M_TO_IN,
                "barrel_path_from_onset_in": onset_path_m * M_TO_IN,
                "barrel_path_final150ms_in": final150_path_m * M_TO_IN,
                "barrel_avg_speed_500ms_mph": safe_div(full_path_m, t[contact_i] - t[start_i]) * MPS_TO_MPH,
                "barrel_avg_speed_from_onset_mph": safe_div(onset_path_m, t[contact_i] - t[onset_i]) * MPS_TO_MPH,
                "barrel_peak_speed_mph": speed_mps[peak_i] * MPS_TO_MPH,
                "barrel_peak_speed_time": t[peak_i],
                "barrel_peak_speed_ms_before_contact": (contact - t[peak_i]) * 1000.0,
                "sweet_spot_contact_x": contact_pos[0],
                "sweet_spot_contact_y": contact_pos[1],
                "sweet_spot_contact_z": contact_pos[2],
                "contact_forward_from_thorax_in": (contact_pos[0] - thorax_contact[0]) * M_TO_IN,
                "contact_vertical_from_thorax_in": (contact_pos[2] - thorax_contact[2]) * M_TO_IN,
            }
        )
    return pd.DataFrame(rows)


def calculate_all_onsets(
    landmarks: pd.DataFrame,
    joint_velos: pd.DataFrame,
    metadata: pd.DataFrame,
    primary_config: OnsetConfig,
    sensitivity_configs: list[OnsetConfig],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    primary_rows = []
    sensitivity_rows = []

    landmark_groups = dict(tuple(landmarks.groupby("session_swing", sort=False)))
    velo_groups = dict(tuple(joint_velos.groupby("session_swing", sort=False)))
    side_map = (
        metadata.assign(session_swing=metadata["session_swing"].astype(str))
        .set_index("session_swing")["hitter_side"]
        .astype(str)
        .str.upper()
        .to_dict()
    )
    for sid, lg in landmark_groups.items():
        vg = velo_groups.get(sid)
        if vg is None:
            primary_rows.append({"session_swing": sid, "onset_qc": "missing_joint_velos"})
            continue
        segment_signals = build_segment_signals(lg, vg, side_map.get(str(sid), ""))
        primary = summarize_onsets(sid, segment_signals, primary_config)
        primary_rows.append(primary)
        for config in sensitivity_configs:
            sens = summarize_onsets(sid, segment_signals, config)
            sensitivity_rows.append(
                {
                    "session_swing": sid,
                    "config": config.label,
                    "composite_swing_time_ms": sens.get("composite_swing_time_ms"),
                    "initiation_spread_ms": sens.get("initiation_spread_ms"),
                    "detected_segment_count": sens.get("detected_segment_count"),
                    "onset_qc": sens.get("onset_qc"),
                }
            )
    return pd.DataFrame(primary_rows), pd.DataFrame(sensitivity_rows)


def build_segment_signals(
    lg: pd.DataFrame, vg: pd.DataFrame, hitter_side: str
) -> dict[str, dict[str, object]]:
    contact = first_numeric(lg["contact_time"])
    fp10 = first_numeric(lg["fp_10_time"]) if "fp_10_time" in lg else np.nan
    out: dict[str, dict[str, object]] = {}

    vg = vg.sort_values("time")
    vt = vg["time"].to_numpy(float)
    if not np.isfinite(contact) and "contact_time" in vg:
        contact = first_numeric(vg["contact_time"])
    if not np.isfinite(fp10) and "fp_10_time" in vg:
        fp10 = first_numeric(vg["fp_10_time"])

    for segment, cols in ANGULAR_ONSET_COLS.items():
        if set(cols).issubset(vg.columns):
            out[segment] = {
                "kind": "piecewise_accel_burst_onset",
                "segment": segment,
                "time": vt,
                "angular_velocity": vg[cols].apply(pd.to_numeric, errors="coerce").to_numpy(float),
                "contact": contact,
                "fp10": fp10,
                "window_end": "angular_velocity_peak" if segment in {"pelvis", "torso"} else "contact",
                "peak_rule": "first_after_fp10" if segment == "lead_arm" else "largest",
                "burst_peak_rule": primary_burst_peak_rule(segment),
                "burst_peak_threshold_pct": primary_burst_peak_threshold(segment, PRIMARY_CONFIG),
                "burst_reference_ms_before_contact": primary_burst_reference_ms(segment, PRIMARY_CONFIG),
                "burst_window_ms": primary_burst_window_ms(segment),
            }
            if segment == "lead_hand":
                hand_prefix = lead_hand_marker_prefix(hitter_side)
                hand_cols = [f"{hand_prefix}_{axis}" for axis in ("x", "y", "z")] if hand_prefix else []
                if hand_cols and set(hand_cols).issubset(lg.columns):
                    out[segment]["kind"] = "lead_hand_hybrid_direction_accel"
                    out[segment]["landmark_time"] = lg["time"].apply(pd.to_numeric, errors="coerce").to_numpy(float)
                    out[segment]["lead_hand_xyz"] = lg[hand_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
                elbow_cross_time = detect_lead_elbow_back_shoulder_cross_time(
                    lg,
                    hitter_side,
                    contact,
                    PRIMARY_CONFIG,
                )
                wrist_cross_time = detect_lead_wrist_back_shoulder_cross_time(
                    lg,
                    hitter_side,
                    contact,
                    PRIMARY_CONFIG,
                )
                shoulder_cross_time = elbow_cross_time if np.isfinite(elbow_cross_time) else wrist_cross_time
                if np.isfinite(shoulder_cross_time):
                    cross_source = (
                        "lead_elbow_back_shoulder_cross"
                        if np.isfinite(elbow_cross_time)
                        else "lead_wrist_back_shoulder_cross"
                    )
                    out[segment]["burst_window_time"] = (
                        contact + LEAD_HAND_BURST_WINDOW_MS[0] / 1000.0,
                        shoulder_cross_time,
                    )
                    out[segment]["burst_window_label"] = f"200ms_to_{cross_source}"
                    out[segment]["lead_elbow_back_shoulder_cross_time"] = elbow_cross_time
                    out[segment]["lead_wrist_back_shoulder_cross_time"] = wrist_cross_time
                    out[segment]["lead_hand_selected_back_shoulder_cross_time"] = shoulder_cross_time
                    out[segment]["lead_hand_search_window_end_source"] = cross_source

    return out


def summarize_onsets(
    sid: str, segment_signals: dict[str, dict[str, object]], config: OnsetConfig
) -> dict[str, float | str | int]:
    rows: dict[str, float | str | int] = {"session_swing": sid}
    contacts = [v["contact"] for v in segment_signals.values() if np.isfinite(v["contact"])]
    contact = float(contacts[0]) if contacts else np.nan
    if not np.isfinite(contact):
        rows["onset_qc"] = "missing_contact"
        return rows

    onset_times = []
    initiation_onset_times = []
    for segment, data in segment_signals.items():
        onset, method, inflection = detect_segment_onset(data, config)
        rows[f"{segment}_onset_time"] = onset
        rows[f"{segment}_to_contact_ms"] = (contact - onset) * 1000.0 if np.isfinite(onset) else np.nan
        rows[f"{segment}_inflection_time"] = inflection
        rows[f"{segment}_inflection_to_contact_ms"] = (
            (contact - inflection) * 1000.0 if np.isfinite(inflection) else np.nan
        )
        rows[f"{segment}_onset_method"] = method
        if segment == "lead_hand":
            window_start = contact + LEAD_HAND_BURST_WINDOW_MS[0] / 1000.0
            cross_time = float(data.get("lead_hand_selected_back_shoulder_cross_time", np.nan))
            window_end = cross_time if np.isfinite(cross_time) else contact + LEAD_HAND_BURST_WINDOW_MS[1] / 1000.0
            rows["lead_hand_search_window_start_time"] = window_start
            rows["lead_hand_search_window_end_time"] = window_end
            rows["lead_hand_search_window_start_ms"] = (window_start - contact) * 1000.0
            rows["lead_hand_search_window_end_ms"] = (window_end - contact) * 1000.0
            rows["lead_hand_search_window_end_source"] = (
                data.get("lead_hand_search_window_end_source", "fallback_100ms")
                if np.isfinite(cross_time)
                else "fallback_100ms"
            )
            if "lead_hand_hybrid_load_back" in str(method):
                rows["lead_hand_onset_strategy"] = "load_back_first_forward_move"
            elif "lead_hand_hybrid_drift_forward" in str(method):
                rows["lead_hand_onset_strategy"] = "drift_forward_accel_jump"
            elif np.isfinite(onset):
                rows["lead_hand_onset_strategy"] = "other"
            else:
                rows["lead_hand_onset_strategy"] = "not_detected"
        if np.isfinite(onset):
            onset_times.append(onset)
            if segment in INITIATION_SEGMENTS:
                initiation_onset_times.append(onset)

    rows["detected_segment_count"] = len(onset_times)
    rows["detected_initiation_segment_count"] = len(initiation_onset_times)
    if not onset_times:
        rows["onset_qc"] = "no_segments_detected"
        return rows
    if not initiation_onset_times:
        rows["onset_qc"] = "no_initiation_segments_detected"
        return rows

    earliest = min(initiation_onset_times)
    latest = max(initiation_onset_times)
    rows["composite_onset_time"] = earliest
    rows["latest_onset_time"] = latest
    rows["composite_swing_time_ms"] = (contact - earliest) * 1000.0
    rows["initiation_spread_ms"] = (latest - earliest) * 1000.0
    rows["onset_qc"] = "ok" if len(initiation_onset_times) == len(INITIATION_SEGMENTS) else "few_initiation_segments_detected"
    return rows


def detect_segment_onset(data: dict[str, object], config: OnsetConfig) -> tuple[float, str, float]:
    kind = str(data.get("kind", "legacy_threshold"))
    contact = float(data.get("contact", np.nan))

    if kind == "velocity_peak":
        onset = detect_first_velocity_peak_onset(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["xyz"], dtype=float),
            contact,
            config,
            tuple(data.get("axes", (0, 2))),
        )
        if np.isfinite(onset):
            axes = tuple(data.get("axes", (0, 2)))
            return onset, f"first_velocity_peak_{axis_label(axes)}", onset

        fallback = directional_velocity_to_contact(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["xyz"], dtype=float),
            contact,
        )
        onset = detect_onset(np.asarray(data["time"], dtype=float), fallback, contact, config)
        return onset, "legacy_velocity_threshold_fallback" if np.isfinite(onset) else "not_detected", np.nan

    if kind == "path_inflection":
        gate_pct = float(data.get("path_turn_velocity_gate_pct", config.path_turn_velocity_gate_pct))
        onset, inflection = detect_path_inflection_onset(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["xyz"], dtype=float),
            contact,
            config,
            tuple(data.get("axes", (0, 2))),
            gate_pct,
        )
        if np.isfinite(onset):
            axes = tuple(data.get("axes", (0, 2)))
            gate_label = int(round(gate_pct * 100))
            return onset, f"last_path_turn_before_{gate_label}pct_velocity_{axis_label(axes)}", inflection

        return np.nan, "not_detected", np.nan

    if kind == "angular_accel_peak":
        onset, method_suffix = detect_angular_accel_peak_onset_details(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["angular_velocity"], dtype=float),
            contact,
            config,
            str(data.get("window_end", "contact")),
            str(data.get("peak_rule", "largest")),
            float(data.get("fp10", np.nan)),
        )
        method = f"signed_angular_accel_peak_{method_suffix}"
        return onset, method if np.isfinite(onset) else "not_detected", onset

    if kind == "piecewise_velocity_change_point":
        onset, velocity_peak = detect_piecewise_velocity_onset(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["angular_velocity"], dtype=float),
            contact,
            config,
        )
        method = "piecewise_3d_angular_velocity_change_point"
        return onset, method if np.isfinite(onset) else "not_detected", onset

    if kind == "piecewise_accel_burst_onset":
        onset, piecewise_start, velocity_peak = detect_piecewise_accel_burst_onset(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["angular_velocity"], dtype=float),
            contact,
            config,
            burst_peak_rule=str(data.get("burst_peak_rule", "largest")),
            burst_peak_threshold_pct=float(data.get("burst_peak_threshold_pct", config.burst_peak_threshold_pct)),
            burst_reference_ms_before_contact=float(
                data.get("burst_reference_ms_before_contact", config.burst_reference_ms_before_contact)
            ),
            burst_window_ms=data.get("burst_window_ms"),
            burst_window_time=data.get("burst_window_time"),
        )
        method = "piecewise_gated_peak_signed_angular_accel"
        burst_peak_rule = str(data.get("burst_peak_rule", "largest"))
        if burst_peak_rule == "first_above_threshold":
            threshold_pct = float(data.get("burst_peak_threshold_pct", config.burst_peak_threshold_pct))
            method += f"_first_{int(round(threshold_pct * 100))}pct_peak"
        elif burst_peak_rule == "last_before_largest_above_threshold":
            threshold_pct = float(data.get("burst_peak_threshold_pct", config.burst_peak_threshold_pct))
            method += f"_last_before_100pct_peak_above_{int(round(threshold_pct * 100))}pct"
        elif burst_peak_rule == "closest_to_reference":
            threshold_pct = float(data.get("burst_peak_threshold_pct", config.burst_peak_threshold_pct))
            reference_ms = float(
                data.get("burst_reference_ms_before_contact", config.burst_reference_ms_before_contact)
            )
            method += f"_closest_to_{reference_ms:.1f}ms_among_{int(round(threshold_pct * 100))}pct_peaks"
        burst_window_ms = data.get("burst_window_ms")
        burst_window_time = data.get("burst_window_time")
        burst_window_label = data.get("burst_window_label")
        if isinstance(burst_window_time, tuple) and len(burst_window_time) == 2 and isinstance(burst_window_label, str):
            method += f"_window_{burst_window_label}"
        elif isinstance(burst_window_ms, tuple) and len(burst_window_ms) == 2:
            start_ms, end_ms = burst_window_ms
            method += f"_window_{abs(int(round(float(start_ms))))}to{abs(int(round(float(end_ms))))}ms"
        return onset, method if np.isfinite(onset) else "not_detected", onset

    if kind == "lead_elbow_negative_accel_peak_for_lead_hand":
        onset = detect_lead_elbow_negative_accel_peak_onset(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["lead_elbow_angular_velocity"], dtype=float),
            contact,
            config,
            burst_window_ms=data.get("burst_window_ms"),
            burst_window_time=data.get("burst_window_time"),
            window_end_source=str(data.get("lead_hand_search_window_end_source", "")),
        )
        method = "lead_elbow_peak_negative_signed_angular_accel_for_lead_hand"
        burst_window_label = data.get("burst_window_label")
        if isinstance(data.get("burst_window_time"), tuple) and isinstance(burst_window_label, str):
            method += f"_window_{burst_window_label}"
        elif isinstance(data.get("burst_window_ms"), tuple):
            start_ms, end_ms = data["burst_window_ms"]
            method += f"_window_{abs(int(round(float(start_ms))))}to{abs(int(round(float(end_ms))))}ms"
        return onset, method if np.isfinite(onset) else "not_detected", onset

    if kind == "lead_hand_hybrid_direction_accel":
        onset, strategy = detect_lead_hand_hybrid_direction_accel_onset(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["angular_velocity"], dtype=float),
            np.asarray(data["landmark_time"], dtype=float),
            np.asarray(data["lead_hand_xyz"], dtype=float),
            contact,
            config,
            burst_window_ms=data.get("burst_window_ms"),
            burst_window_time=data.get("burst_window_time"),
        )
        method = f"lead_hand_hybrid_{strategy}"
        burst_window_label = data.get("burst_window_label")
        if isinstance(data.get("burst_window_time"), tuple) and isinstance(burst_window_label, str):
            method += f"_window_{burst_window_label}"
        elif isinstance(data.get("burst_window_ms"), tuple):
            start_ms, end_ms = data["burst_window_ms"]
            method += f"_window_{abs(int(round(float(start_ms))))}to{abs(int(round(float(end_ms))))}ms"
        return onset, method if np.isfinite(onset) else "not_detected", onset

    if kind == "barrel_x_reversal":
        onset, reversal = detect_barrel_x_reversal_onset(
            np.asarray(data["time"], dtype=float),
            np.asarray(data["xyz"], dtype=float),
            contact,
            config,
        )
        if np.isfinite(onset):
            return onset, "barrel_x_reversal_toward_catcher_top_view", reversal
        fallback = data.get("fallback")
        if isinstance(fallback, dict):
            fallback_onset, fallback_method, fallback_inflection = detect_segment_onset(fallback, config)
            if np.isfinite(fallback_onset):
                return fallback_onset, f"fallback_{fallback_method}", fallback_inflection
        return np.nan, "not_detected", np.nan

    onset = detect_onset(
        np.asarray(data["time"], dtype=float),
        np.asarray(data["signal"], dtype=float),
        contact,
        config,
    )
    return onset, "legacy_velocity_threshold" if np.isfinite(onset) else "not_detected", np.nan


def detect_angular_accel_peak_onset(
    time: np.ndarray,
    angular_velocity: np.ndarray,
    contact: float,
    config: OnsetConfig,
    window_end: str,
    peak_rule: str = "largest",
    fp10: float = np.nan,
) -> float:
    onset, _ = detect_angular_accel_peak_onset_details(
        time,
        angular_velocity,
        contact,
        config,
        window_end,
        peak_rule,
        fp10,
    )
    return onset


def detect_piecewise_velocity_onset(
    time: np.ndarray,
    angular_velocity: np.ndarray,
    contact: float,
    config: OnsetConfig,
) -> tuple[float, float]:
    valid = np.isfinite(time) & np.isfinite(angular_velocity).all(axis=1)
    time = time[valid]
    angular_velocity = angular_velocity[valid]
    if len(time) < 18 or not np.isfinite(contact):
        return np.nan, np.nan

    mask = (time >= contact - config.search_back_s) & (time <= contact)
    if mask.sum() < 18:
        return np.nan, np.nan
    t = time[mask]
    omega = angular_velocity[mask]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan, np.nan

    omega_mag = np.linalg.norm(omega, axis=1)
    omega_mag = smooth_positions(omega_mag[:, None], dt, config.smooth_ms).ravel()

    contact_limit = contact - config.min_precontact_ms / 1000.0
    eligible = np.where(t <= contact_limit)[0]
    if len(eligible) < 12:
        eligible = np.arange(len(t))
    if len(eligible) < 12:
        return np.nan, np.nan

    peak_i = int(eligible[np.nanargmax(omega_mag[eligible])])
    if peak_i < 16:
        return np.nan, float(t[peak_i]) if np.isfinite(omega_mag[peak_i]) else np.nan

    min_points_per_side = max(6, int(round(0.020 / dt)))
    if peak_i < min_points_per_side * 2:
        return np.nan, float(t[peak_i]) if np.isfinite(omega_mag[peak_i]) else np.nan

    y = omega_mag[: peak_i + 1]
    x = t[: peak_i + 1]
    valid_fit = np.isfinite(x) & np.isfinite(y)
    if valid_fit.sum() < min_points_per_side * 2 + 1:
        return np.nan, float(t[peak_i])

    single_sse, _ = fit_single_line(x[valid_fit], y[valid_fit])
    best = None
    max_onset_time = contact - 0.030
    for tau_i in range(min_points_per_side, peak_i - min_points_per_side + 1):
        if not valid_fit[tau_i] or t[tau_i] > max_onset_time:
            continue
        left_count = int(valid_fit[: tau_i + 1].sum())
        right_count = int(valid_fit[tau_i:].sum())
        if left_count < min_points_per_side or right_count < min_points_per_side:
            continue

        tau = t[tau_i]
        sse, coef, _ = fit_hinge(x[valid_fit], y[valid_fit], tau)
        if not np.isfinite(sse):
            continue
        slope_before = float(coef[1])
        slope_after = float(coef[1] + coef[2])
        added_slope = float(coef[2])
        if slope_after <= 0 or added_slope <= 0:
            continue
        if best is None or sse < best["sse"]:
            best = {"tau_i": tau_i, "sse": sse}

    if best is None or not np.isfinite(single_sse) or single_sse <= 0:
        return np.nan, float(t[peak_i])

    return float(t[int(best["tau_i"])]), float(t[peak_i])


def detect_piecewise_accel_burst_onset(
    time: np.ndarray,
    angular_velocity: np.ndarray,
    contact: float,
    config: OnsetConfig,
    burst_peak_rule: str = "largest",
    burst_peak_threshold_pct: float | None = None,
    burst_reference_ms_before_contact: float | None = None,
    burst_window_ms: tuple[float, float] | None = None,
    burst_window_time: tuple[float, float] | None = None,
) -> tuple[float, float, float]:
    piecewise_start, velocity_peak = detect_piecewise_velocity_onset(time, angular_velocity, contact, config)
    if not np.isfinite(piecewise_start) or not np.isfinite(velocity_peak):
        return np.nan, piecewise_start, velocity_peak

    valid = np.isfinite(time) & np.isfinite(angular_velocity).all(axis=1)
    time = time[valid]
    angular_velocity = angular_velocity[valid]
    if len(time) < 18:
        return np.nan, piecewise_start, velocity_peak

    mask = (time >= contact - config.search_back_s) & (time <= contact)
    if mask.sum() < 18:
        return np.nan, piecewise_start, velocity_peak
    t = time[mask]
    omega = angular_velocity[mask]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan, piecewise_start, velocity_peak

    omega_mag = np.linalg.norm(omega, axis=1)
    omega_mag = smooth_positions(omega_mag[:, None], dt, config.smooth_ms).ravel()
    signed_accel = np.gradient(omega_mag, t)
    signed_accel = smooth_positions(signed_accel[:, None], dt, config.smooth_ms).ravel()

    using_absolute_window = isinstance(burst_window_time, tuple) and len(burst_window_time) == 2
    if using_absolute_window:
        start_time, end_time = sorted(float(v) for v in burst_window_time)
        end_time = min(end_time, contact - config.min_precontact_ms / 1000.0)
        accel_window = np.where((t >= start_time) & (t < end_time))[0]
        if len(accel_window) < 5 and isinstance(burst_window_ms, tuple) and len(burst_window_ms) == 2:
            start_ms, end_ms = sorted(float(v) for v in burst_window_ms)
            rel_ms = (t - contact) * 1000.0
            accel_window = np.where((rel_ms >= start_ms) & (rel_ms <= end_ms))[0]
    elif isinstance(burst_window_ms, tuple) and len(burst_window_ms) == 2:
        start_ms, end_ms = sorted(float(v) for v in burst_window_ms)
        rel_ms = (t - contact) * 1000.0
        accel_window = np.where((rel_ms >= start_ms) & (rel_ms <= end_ms))[0]
    else:
        onset_i = int(np.searchsorted(t, piecewise_start, side="left"))
        peak_i = int(np.nanargmin(np.abs(t - velocity_peak)))
        start_i = max(1, min(onset_i, len(t) - 1))
        stop_i = max(start_i, min(peak_i, len(t) - 1))
        accel_window = np.arange(start_i, stop_i + 1)
    accel_window = accel_window[np.isfinite(signed_accel[accel_window])]
    accel_window = accel_window[signed_accel[accel_window] > 0]
    if len(accel_window) == 0:
        return np.nan, piecewise_start, velocity_peak

    if burst_peak_rule in {"first_above_threshold", "closest_to_reference", "last_before_largest_above_threshold"}:
        threshold_pct = config.burst_peak_threshold_pct if burst_peak_threshold_pct is None else burst_peak_threshold_pct
        threshold_pct = max(0.0, min(float(threshold_pct), 1.0))
        max_accel = float(np.nanmax(signed_accel[accel_window]))
        threshold = threshold_pct * max_accel
        local_peaks = local_positive_peaks(signed_accel, accel_window)
        qualifying = [i for i in local_peaks if signed_accel[i] >= threshold]
        if qualifying:
            if burst_peak_rule == "closest_to_reference":
                reference_ms = (
                    config.burst_reference_ms_before_contact
                    if burst_reference_ms_before_contact is None
                    else float(burst_reference_ms_before_contact)
                )
                burst_i = min(qualifying, key=lambda i: abs(((contact - t[i]) * 1000.0) - reference_ms))
            elif burst_peak_rule == "last_before_largest_above_threshold":
                largest_i = int(accel_window[np.nanargmax(signed_accel[accel_window])])
                prior_qualifying = [i for i in qualifying if i < largest_i]
                burst_i = int(prior_qualifying[-1]) if prior_qualifying else largest_i
            else:
                burst_i = int(qualifying[0])
            return float(t[burst_i]), piecewise_start, velocity_peak

    burst_i = int(accel_window[np.nanargmax(signed_accel[accel_window])])
    return float(t[burst_i]), piecewise_start, velocity_peak


def detect_lead_elbow_back_shoulder_cross_time(
    landmarks: pd.DataFrame,
    hitter_side: str,
    contact: float,
    config: OnsetConfig,
) -> float:
    return detect_lead_marker_back_shoulder_cross_time(
        landmarks,
        hitter_side,
        contact,
        config,
        {
            "R": ("lejc_x", "rsjc_x"),
            "L": ("rejc_x", "lsjc_x"),
        },
    )


def lead_hand_marker_prefix(hitter_side: str) -> str | None:
    side = str(hitter_side).upper()
    if side == "R":
        return "lhjc"
    if side == "L":
        return "rhjc"
    return None


def detect_lead_wrist_back_shoulder_cross_time(
    landmarks: pd.DataFrame,
    hitter_side: str,
    contact: float,
    config: OnsetConfig,
) -> float:
    return detect_lead_marker_back_shoulder_cross_time(
        landmarks,
        hitter_side,
        contact,
        config,
        {
            "R": ("lwjc_x", "rsjc_x"),
            "L": ("rwjc_x", "lsjc_x"),
        },
    )


def detect_lead_marker_back_shoulder_cross_time(
    landmarks: pd.DataFrame,
    hitter_side: str,
    contact: float,
    config: OnsetConfig,
    marker_map: dict[str, tuple[str, str]],
) -> float:
    side = str(hitter_side).upper()
    markers = marker_map.get(side)
    if markers is None or not np.isfinite(contact):
        return np.nan
    marker_col, shoulder_col = markers
    needed = {"time", marker_col, shoulder_col}
    if not needed.issubset(landmarks.columns):
        return np.nan

    g = landmarks.sort_values("time").copy()
    for col in needed:
        g[col] = pd.to_numeric(g[col], errors="coerce")
    time = g["time"].to_numpy(float)
    marker_x = g[marker_col].to_numpy(float)
    shoulder_x = g[shoulder_col].to_numpy(float)
    valid = np.isfinite(time) & np.isfinite(marker_x) & np.isfinite(shoulder_x)
    if valid.sum() < 8:
        return np.nan
    time = time[valid]
    relative_x = marker_x[valid] - shoulder_x[valid]

    start = contact + LEAD_HAND_BURST_WINDOW_MS[0] / 1000.0
    end = contact - config.min_precontact_ms / 1000.0
    mask = (time >= start) & (time <= end)
    if mask.sum() < 8:
        return np.nan
    t = time[mask]
    rel = relative_x[mask]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan
    rel = smooth_positions(rel[:, None], dt, config.smooth_ms).ravel()

    tail = rel[-max(3, int(round(0.025 / dt))) :]
    final_value = float(np.nanmedian(tail))
    if not np.isfinite(final_value) or abs(final_value) <= 1e-6:
        return np.nan
    final_sign = 1.0 if final_value > 0 else -1.0

    for i in range(1, len(t)):
        prev = rel[i - 1]
        curr = rel[i]
        if not np.isfinite(prev) or not np.isfinite(curr):
            continue
        if prev * final_sign <= 0 < curr * final_sign:
            denom = curr - prev
            if abs(denom) > 1e-9:
                fraction = float(np.clip((0.0 - prev) / denom, 0.0, 1.0))
                return float(t[i - 1] + fraction * (t[i] - t[i - 1]))
            return float(t[i])

    return np.nan


def detect_barrel_x_reversal_onset(
    time: np.ndarray,
    xyz: np.ndarray,
    contact: float,
    config: OnsetConfig,
) -> tuple[float, float]:
    valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
    time = time[valid]
    xyz = xyz[valid]
    if len(time) < 18 or not np.isfinite(contact):
        return np.nan, np.nan

    mask = (time >= contact - config.search_back_s) & (time <= contact - config.min_precontact_ms / 1000.0)
    if mask.sum() < 18:
        return np.nan, np.nan
    t = time[mask]
    x = xyz[mask, 0]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan, np.nan

    x = smooth_positions(x[:, None], dt, config.smooth_ms).ravel()
    x_velocity = np.gradient(x, t)
    rel_ms = (t - contact) * 1000.0

    ref_start, ref_end = LEAD_HAND_BARREL_REVERSAL_REFERENCE_WINDOW_MS
    ref_mask = (rel_ms >= ref_start) & (rel_ms <= ref_end) & np.isfinite(x_velocity)
    if ref_mask.sum() < 5:
        ref_mask = (rel_ms >= -150.0) & (rel_ms <= -50.0) & np.isfinite(x_velocity)
    if ref_mask.sum() < 5:
        return np.nan, np.nan

    rearward_velocity = float(np.nanmedian(x_velocity[ref_mask]))
    if not np.isfinite(rearward_velocity) or abs(rearward_velocity) <= 1e-6:
        return np.nan, np.nan
    rearward_sign = 1.0 if rearward_velocity > 0 else -1.0

    search_start, search_end = LEAD_HAND_BARREL_REVERSAL_SEARCH_WINDOW_MS
    search_indices = np.where((rel_ms >= search_start) & (rel_ms <= search_end))[0]
    if len(search_indices) < 8:
        return np.nan, np.nan

    pre_window = max(2, int(round(0.012 / dt)))
    sustain_frames = max(3, int(round((LEAD_HAND_BARREL_REVERSAL_SUSTAIN_MS / 1000.0) / dt)))
    min_rearward_displacement_m = 0.005
    candidates: list[int] = []
    for i in search_indices:
        if i - pre_window < 0 or i + sustain_frames >= len(t):
            continue
        before = float(np.nanmedian(x_velocity[i - pre_window : i]))
        after = float(np.nanmedian(x_velocity[i : i + sustain_frames]))
        displacement = float((x[i + sustain_frames] - x[i]) * rearward_sign)
        if not np.isfinite(before) or not np.isfinite(after) or not np.isfinite(displacement):
            continue
        if before * rearward_sign < 0 and after * rearward_sign > 0 and displacement >= min_rearward_displacement_m:
            candidates.append(int(i))

    if not candidates:
        return np.nan, np.nan

    candidate = candidates[-1]
    return float(t[candidate]), float(t[candidate])


def primary_burst_peak_rule(segment: str) -> str:
    if segment == "pelvis":
        return "closest_to_reference"
    if segment == "lead_hand":
        return "last_before_largest_above_threshold"
    return "largest"


def primary_burst_peak_threshold(segment: str, config: OnsetConfig) -> float:
    if segment == "pelvis":
        return config.burst_peak_threshold_pct
    if segment == "lead_hand":
        return LEAD_HAND_BURST_THRESHOLD_PCT
    return np.nan


def primary_burst_reference_ms(segment: str, config: OnsetConfig) -> float:
    if segment == "pelvis":
        return config.burst_reference_ms_before_contact
    return np.nan


def primary_burst_window_ms(segment: str) -> tuple[float, float] | None:
    if segment == "lead_hand":
        return LEAD_HAND_BURST_WINDOW_MS
    return None


def local_positive_peaks(signal: np.ndarray, candidate_indices: np.ndarray) -> list[int]:
    candidates = set(int(i) for i in candidate_indices)
    peaks: list[int] = []
    for i in sorted(candidates):
        if i <= 0 or i >= len(signal) - 1:
            continue
        if not np.isfinite(signal[i]) or signal[i] <= 0:
            continue
        if signal[i] >= signal[i - 1] and signal[i] >= signal[i + 1]:
            peaks.append(i)
    return peaks


def local_negative_peaks(signal: np.ndarray, candidate_indices: np.ndarray) -> list[int]:
    candidates = set(int(i) for i in candidate_indices)
    peaks: list[int] = []
    for i in sorted(candidates):
        if i <= 0 or i >= len(signal) - 1:
            continue
        if not np.isfinite(signal[i]) or signal[i] >= 0:
            continue
        if signal[i] <= signal[i - 1] and signal[i] <= signal[i + 1]:
            peaks.append(i)
    return peaks


def detect_lead_elbow_negative_accel_peak_onset(
    time: np.ndarray,
    angular_velocity: np.ndarray,
    contact: float,
    config: OnsetConfig,
    burst_window_ms: tuple[float, float] | None = None,
    burst_window_time: tuple[float, float] | None = None,
    window_end_source: str = "",
) -> float:
    valid = np.isfinite(time) & np.isfinite(angular_velocity).all(axis=1)
    time = time[valid]
    angular_velocity = angular_velocity[valid]
    if len(time) < 18 or not np.isfinite(contact):
        return np.nan

    mask = (time >= contact - config.search_back_s) & (time <= contact)
    if mask.sum() < 18:
        return np.nan
    t = time[mask]
    omega = angular_velocity[mask]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan

    omega_mag = np.linalg.norm(omega, axis=1)
    omega_mag = smooth_positions(omega_mag[:, None], dt, config.smooth_ms).ravel()
    signed_accel = np.gradient(omega_mag, t)
    signed_accel = smooth_positions(signed_accel[:, None], dt, config.smooth_ms).ravel()

    end_time = np.nan
    if isinstance(burst_window_time, tuple) and len(burst_window_time) == 2:
        start_time, end_time = sorted(float(v) for v in burst_window_time)
        end_time = min(end_time, contact - config.min_precontact_ms / 1000.0)
        accel_window = np.where((t >= start_time) & (t < end_time))[0]
        if len(accel_window) < 5 and isinstance(burst_window_ms, tuple) and len(burst_window_ms) == 2:
            start_ms, end_ms = sorted(float(v) for v in burst_window_ms)
            rel_ms = (t - contact) * 1000.0
            accel_window = np.where((rel_ms >= start_ms) & (rel_ms <= end_ms))[0]
            end_time = contact + end_ms / 1000.0
    elif isinstance(burst_window_ms, tuple) and len(burst_window_ms) == 2:
        start_ms, end_ms = sorted(float(v) for v in burst_window_ms)
        rel_ms = (t - contact) * 1000.0
        accel_window = np.where((rel_ms >= start_ms) & (rel_ms <= end_ms))[0]
        end_time = contact + end_ms / 1000.0
    else:
        rel_ms = (t - contact) * 1000.0
        accel_window = np.where((rel_ms >= LEAD_HAND_BURST_WINDOW_MS[0]) & (rel_ms <= LEAD_HAND_BURST_WINDOW_MS[1]))[0]
        end_time = contact + LEAD_HAND_BURST_WINDOW_MS[1] / 1000.0

    accel_window = accel_window[np.isfinite(signed_accel[accel_window])]
    accel_window = accel_window[signed_accel[accel_window] < 0]
    if len(accel_window) == 0:
        return np.nan

    local_peaks = local_negative_peaks(signed_accel, accel_window)
    if local_peaks:
        peak_i = int(min(local_peaks, key=lambda i: signed_accel[i]))
        if (
            window_end_source == "lead_wrist_back_shoulder_cross"
            and np.isfinite(end_time)
            and end_time - t[peak_i] <= max(0.010, 3.0 * dt)
        ):
            prior = [i for i in local_peaks if i < peak_i]
            if prior:
                peak_i = int(prior[-1])
    else:
        peak_i = int(accel_window[np.nanargmin(signed_accel[accel_window])])

    return float(t[peak_i])


def detect_lead_hand_hybrid_direction_accel_onset(
    angular_time: np.ndarray,
    angular_velocity: np.ndarray,
    landmark_time: np.ndarray,
    lead_hand_xyz: np.ndarray,
    contact: float,
    config: OnsetConfig,
    burst_window_ms: tuple[float, float] | None = None,
    burst_window_time: tuple[float, float] | None = None,
) -> tuple[float, str]:
    window_start, window_end = lead_hand_window_bounds(contact, config, burst_window_ms, burst_window_time)
    onset, is_load_back = detect_lead_hand_load_back_forward_move(
        landmark_time,
        lead_hand_xyz,
        window_start,
        window_end,
        config,
    )
    if is_load_back:
        return onset, "load_back_first_forward_move" if np.isfinite(onset) else "load_back_not_detected"

    onset = detect_lead_hand_drift_forward_linear_accel_jump(
        landmark_time,
        lead_hand_xyz,
        window_start,
        window_end,
        config,
    )
    return onset, "drift_forward_linear_accel_jump_15pct" if np.isfinite(onset) else "drift_forward_not_detected"


def lead_hand_window_bounds(
    contact: float,
    config: OnsetConfig,
    burst_window_ms: tuple[float, float] | None = None,
    burst_window_time: tuple[float, float] | None = None,
) -> tuple[float, float]:
    if isinstance(burst_window_time, tuple) and len(burst_window_time) == 2:
        start_time, end_time = sorted(float(v) for v in burst_window_time)
        return start_time, min(end_time, contact - config.min_precontact_ms / 1000.0)
    if isinstance(burst_window_ms, tuple) and len(burst_window_ms) == 2:
        start_ms, end_ms = sorted(float(v) for v in burst_window_ms)
        return contact + start_ms / 1000.0, min(contact + end_ms / 1000.0, contact - config.min_precontact_ms / 1000.0)
    return (
        contact + LEAD_HAND_BURST_WINDOW_MS[0] / 1000.0,
        min(contact + LEAD_HAND_BURST_WINDOW_MS[1] / 1000.0, contact - config.min_precontact_ms / 1000.0),
    )


def detect_lead_hand_load_back_forward_move(
    time: np.ndarray,
    xyz: np.ndarray,
    window_start: float,
    window_end: float,
    config: OnsetConfig,
) -> tuple[float, bool]:
    valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
    time = time[valid]
    xyz = xyz[valid]
    if len(time) < 12 or not np.isfinite(window_start) or not np.isfinite(window_end):
        return np.nan, False
    mask = (time >= window_start) & (time < window_end)
    if mask.sum() < 10:
        return np.nan, False
    t = time[mask]
    x = xyz[mask, 0]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan, False
    x = smooth_positions(x[:, None], dt, config.smooth_ms).ravel()
    vx = np.gradient(x, t)

    tail_n = max(4, int(round(0.020 / dt)))
    late_velocity = float(np.nanmedian(vx[-tail_n:]))
    if not np.isfinite(late_velocity) or abs(late_velocity) < 1e-6:
        late_velocity = float(x[-1] - x[0])
    if not np.isfinite(late_velocity) or abs(late_velocity) < 1e-6:
        return np.nan, False

    forward_sign = 1.0 if late_velocity > 0 else -1.0
    forward_x = x * forward_sign
    trough_i = int(np.nanargmin(forward_x))
    if trough_i <= 0 or trough_i >= len(t) - 2:
        return np.nan, False

    prior_high = float(np.nanmax(forward_x[: trough_i + 1]))
    rearward_displacement = prior_high - float(forward_x[trough_i])
    if rearward_displacement < LEAD_HAND_LOAD_BACK_MIN_DISPLACEMENT_M:
        return np.nan, False

    forward_velocity = vx * forward_sign
    sustain_n = max(3, int(round(0.010 / dt)))
    for i in range(trough_i + 1, len(t) - sustain_n):
        segment = forward_velocity[i : i + sustain_n]
        if np.isfinite(segment).all() and np.nanmedian(segment) >= LEAD_HAND_FORWARD_VELOCITY_THRESHOLD_MPS:
            return float(t[i]), True

    return float(t[trough_i]), True


def detect_lead_hand_drift_forward_linear_accel_jump(
    time: np.ndarray,
    xyz: np.ndarray,
    window_start: float,
    window_end: float,
    config: OnsetConfig,
) -> float:
    valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
    time = time[valid]
    xyz = xyz[valid]
    if len(time) < 18 or not np.isfinite(window_start) or not np.isfinite(window_end):
        return np.nan
    mask = (time >= window_start) & (time < window_end)
    if mask.sum() < 8:
        return np.nan
    t = time[mask]
    x = xyz[mask, 0]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan
    x = smooth_positions(x[:, None], dt, config.smooth_ms).ravel()
    vx = np.gradient(x, t)
    ax = np.gradient(vx, t)
    ax = smooth_positions(ax[:, None], dt, config.smooth_ms).ravel()

    head_n = max(4, int(round(0.025 / dt)))
    drift_velocity = float(np.nanmedian(vx[:head_n]))
    if not np.isfinite(drift_velocity) or abs(drift_velocity) < 1e-6:
        drift_velocity = float(x[min(head_n, len(x) - 1)] - x[0])
    if not np.isfinite(drift_velocity) or abs(drift_velocity) < 1e-6:
        return np.nan
    drift_sign = 1.0 if drift_velocity > 0 else -1.0
    redirect_accel = -drift_sign * ax

    positive = np.where(np.isfinite(redirect_accel) & (redirect_accel > 0))[0]
    if len(positive) == 0:
        return np.nan
    peak_i = int(positive[np.nanargmax(redirect_accel[positive])])
    peak_accel = float(redirect_accel[peak_i])
    if not np.isfinite(peak_accel) or peak_accel <= 0:
        return np.nan
    threshold = LEAD_HAND_ACCEL_JUMP_THRESHOLD_PCT * peak_accel
    quiet = 0.5 * threshold

    start_i = peak_i
    while start_i > 0 and np.isfinite(redirect_accel[start_i - 1]) and redirect_accel[start_i - 1] > quiet:
        start_i -= 1
    for i in range(start_i, peak_i + 1):
        if np.isfinite(redirect_accel[i]) and redirect_accel[i] >= threshold:
            return float(t[i])
    return float(t[start_i])


def fit_single_line(x: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray]:
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ coef
    return float(np.sum(resid * resid)), coef


def fit_hinge(x: np.ndarray, y: np.ndarray, tau: float) -> tuple[float, np.ndarray, np.ndarray]:
    design = np.column_stack([np.ones(len(x)), x, np.maximum(0.0, x - tau)])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    yhat = design @ coef
    resid = y - yhat
    return float(np.sum(resid * resid)), coef, yhat


def detect_angular_accel_peak_onset_details(
    time: np.ndarray,
    angular_velocity: np.ndarray,
    contact: float,
    config: OnsetConfig,
    window_end: str,
    peak_rule: str = "largest",
    fp10: float = np.nan,
) -> tuple[float, str]:
    valid = np.isfinite(time) & np.isfinite(angular_velocity).all(axis=1)
    time = time[valid]
    angular_velocity = angular_velocity[valid]
    if len(time) < 12 or not np.isfinite(contact):
        return np.nan, f"{peak_rule}_{window_end}"

    mask = (time >= contact - config.search_back_s) & (time <= contact)
    if mask.sum() < 12:
        return np.nan, f"{peak_rule}_{window_end}"
    t = time[mask]
    omega = angular_velocity[mask]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan, f"{peak_rule}_{window_end}"

    omega_mag = np.linalg.norm(omega, axis=1)
    omega_mag = smooth_positions(omega_mag[:, None], dt, config.smooth_ms).ravel()
    signed_accel = np.gradient(omega_mag, t)
    signed_accel = smooth_positions(signed_accel[:, None], dt, config.smooth_ms).ravel()

    contact_limit = contact - config.min_precontact_ms / 1000.0
    eligible = np.where(t <= contact_limit)[0]
    if len(eligible) < 8:
        eligible = np.arange(len(t))
    if window_end == "angular_velocity_peak":
        end_i = int(np.nanargmax(omega_mag[: eligible[-1] + 1]))
    else:
        end_i = int(eligible[-1])
    if end_i < 6:
        return np.nan, f"{peak_rule}_{window_end}"

    min_gap = max(3, int(round(0.020 / dt)))

    def local_positive_peaks(start_i: int, stop_i: int) -> list[int]:
        accel_window = np.arange(start_i, stop_i + 1)
        positive_window = accel_window[np.isfinite(signed_accel[accel_window])]
        local: list[int] = []
        for i in positive_window:
            if i <= 0 or i >= len(signed_accel) - 1:
                continue
            if signed_accel[i] <= 0:
                continue
            if signed_accel[i] >= signed_accel[i - 1] and signed_accel[i] >= signed_accel[i + 1]:
                if local and i - local[-1] < min_gap:
                    if signed_accel[i] > signed_accel[local[-1]]:
                        local[-1] = int(i)
                else:
                    local.append(int(i))
        return local

    def peak_before_largest(local: list[int]) -> int | None:
        if not local:
            return None
        largest_position = max(range(len(local)), key=lambda j: signed_accel[local[j]])
        if largest_position > 0:
            return int(local[largest_position - 1])
        return int(local[largest_position])

    all_local_peaks = local_positive_peaks(1, end_i)
    if peak_rule == "first_after_fp10":
        fp10_valid = (
            np.isfinite(fp10)
            and contact - config.search_back_s <= fp10 < contact - config.min_precontact_ms / 1000.0
        )
        if fp10_valid:
            start_i = max(1, int(np.searchsorted(t, fp10, side="left")))
            local_peaks = local_positive_peaks(start_i, end_i)
            if local_peaks:
                peak_accel_i = int(local_peaks[0])
                if signed_accel[peak_accel_i] <= 0:
                    return np.nan, f"{peak_rule}_{window_end}"
                return float(t[peak_accel_i]), f"{peak_rule}_{window_end}"
            peak_accel_i = peak_before_largest(all_local_peaks)
            method_suffix = f"peak_before_largest_when_no_post_fp10_peak_{window_end}"
        else:
            peak_accel_i = peak_before_largest(all_local_peaks)
            method_suffix = f"peak_before_largest_when_fp10_invalid_{window_end}"
        if peak_accel_i is None or signed_accel[peak_accel_i] <= 0:
            return np.nan, method_suffix
        return float(t[peak_accel_i]), method_suffix

    local_peaks = all_local_peaks
    positive_window = np.arange(1, end_i + 1)
    positive_window = positive_window[np.isfinite(signed_accel[positive_window])]
    if len(positive_window) < 5:
        return np.nan, f"{peak_rule}_{window_end}"

    if local_peaks:
        peak_accel_i = int(max(local_peaks, key=lambda i: signed_accel[i]))
    else:
        peak_accel_i = int(positive_window[np.nanargmax(signed_accel[positive_window])])

    if signed_accel[peak_accel_i] <= 0:
        return np.nan, f"{peak_rule}_{window_end}"
    return float(t[peak_accel_i]), f"{peak_rule}_{window_end}"


def detect_angular_accel_inflection_onset(
    time: np.ndarray,
    angular_velocity: np.ndarray,
    contact: float,
    config: OnsetConfig,
    window_end: str,
) -> float:
    return detect_angular_accel_peak_onset(time, angular_velocity, contact, config, window_end)


def detect_path_inflection_onset(
    time: np.ndarray,
    xyz: np.ndarray,
    contact: float,
    config: OnsetConfig,
    axes: tuple[int, int],
    gate_pct: float | None = None,
) -> tuple[float, float]:
    valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
    time = time[valid]
    xyz = xyz[valid]
    if len(time) < 12 or not np.isfinite(contact):
        return np.nan, np.nan

    mask = (time >= contact - config.search_back_s) & (time <= contact)
    if mask.sum() < 12:
        return np.nan, np.nan
    t = time[mask]
    xy = xyz[mask][:, list(axes)]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan, np.nan

    xy = smooth_positions(xy, dt, config.smooth_ms)
    vx = np.gradient(xy[:, 0], t)
    vy = np.gradient(xy[:, 1], t)
    speed = np.sqrt(vx * vx + vy * vy)

    contact_limit = contact - config.min_precontact_ms / 1000.0
    eligible = np.where(t <= contact_limit)[0]
    if len(eligible) < 8:
        eligible = np.arange(len(t))

    cum_path = np.r_[0.0, np.cumsum(np.sqrt(np.sum(np.diff(xy, axis=0) ** 2, axis=1)))]
    total_path = cum_path[min(eligible[-1], len(cum_path) - 1)]
    if not np.isfinite(total_path) or total_path <= 0:
        return np.nan, np.nan
    path_fraction = cum_path / total_path

    peak_speed_i = int(np.nanargmax(speed[: eligible[-1] + 1]))
    max_speed = float(speed[peak_speed_i])
    if not np.isfinite(max_speed) or max_speed <= 0:
        return np.nan, np.nan
    speed_norm = speed / max_speed
    velocity_gate_i = find_velocity_gate(
        speed_norm,
        peak_speed_i,
        dt,
        config.path_turn_velocity_gate_pct if gate_pct is None else gate_pct,
    )
    search_end = max(eligible[0] + 6, min(eligible[-1], velocity_gate_i))
    if search_end < 8:
        search_end = max(8, min(eligible[-1], velocity_gate_i, peak_speed_i))
    turn_step = max(3, int(round(0.017 / dt)))
    local_gap = max(3, int(round(0.025 / dt)))
    search_idx = np.arange(turn_step, min(search_end, len(t) - turn_step - 1) + 1)
    if len(search_idx) < 5:
        return np.nan, np.nan

    turn_angle = np.full(len(t), np.nan)
    local_motion = np.full(len(t), np.nan)
    turn_score = np.full(len(t), np.nan)
    min_leg_distance = 0.003 * total_path
    for i in search_idx:
        before = xy[i] - xy[i - turn_step]
        after = xy[i + turn_step] - xy[i]
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
    for i in search_idx[1:-1]:
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
        if 0.03 <= path_fraction[i] <= 0.70
        and speed_norm[i] >= 0.02
        and local_motion[i] >= 0.01
        and math.degrees(turn_angle[i]) >= config.path_turn_min_angle_deg
    ]
    if not candidates:
        return np.nan, np.nan

    candidate = int(candidates[-1])
    return float(t[candidate]), float(t[candidate])


def detect_first_velocity_peak_onset(
    time: np.ndarray,
    xyz: np.ndarray,
    contact: float,
    config: OnsetConfig,
    axes: tuple[int, int],
) -> float:
    valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
    time = time[valid]
    xyz = xyz[valid]
    if len(time) < 12 or not np.isfinite(contact):
        return np.nan

    mask = (time >= contact - config.search_back_s) & (time <= contact)
    if mask.sum() < 12:
        return np.nan
    t = time[mask]
    xy = xyz[mask][:, list(axes)]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan

    xy = smooth_positions(xy, dt, config.smooth_ms)
    vx = np.gradient(xy[:, 0], t)
    vy = np.gradient(xy[:, 1], t)
    speed = np.sqrt(vx * vx + vy * vy)

    contact_limit = contact - config.min_precontact_ms / 1000.0
    eligible = np.where(t <= contact_limit)[0]
    if len(eligible) < 8:
        eligible = np.arange(len(t))
    max_speed = float(np.nanmax(speed[eligible]))
    if not np.isfinite(max_speed) or max_speed <= 0:
        return np.nan
    speed_norm = speed / max_speed

    peaks, _ = find_velocity_turns(t, speed_norm, eligible[-1])
    if peaks:
        return float(t[peaks[0]])

    return float(t[int(eligible[int(np.nanargmax(speed_norm[eligible]))])])


def find_velocity_turns(
    time: np.ndarray,
    speed_norm: np.ndarray,
    max_index: int | None = None,
) -> tuple[list[int], list[int]]:
    peaks: list[int] = []
    valleys: list[int] = []
    dt = median_dt(time)
    if not np.isfinite(dt) or dt <= 0:
        return peaks, valleys

    end = len(speed_norm) - 2 if max_index is None else min(max_index, len(speed_norm) - 2)
    lookahead = max(3, int(round(0.080 / dt)))
    min_gap = max(3, int(round(0.025 / dt)))
    min_drop = 0.08

    for i in range(1, end + 1):
        if not np.isfinite(speed_norm[i]):
            continue
        if speed_norm[i] >= speed_norm[i - 1] and speed_norm[i] >= speed_norm[i + 1]:
            after = speed_norm[i + 1 : min(len(speed_norm), i + lookahead + 1)]
            if len(after) and speed_norm[i] - np.nanmin(after) >= min_drop:
                if not peaks or i - peaks[-1] >= min_gap:
                    peaks.append(i)
                elif speed_norm[i] > speed_norm[peaks[-1]]:
                    peaks[-1] = i
        if speed_norm[i] <= speed_norm[i - 1] and speed_norm[i] <= speed_norm[i + 1]:
            before = speed_norm[max(0, i - lookahead) : i]
            after = speed_norm[i + 1 : min(len(speed_norm), i + lookahead + 1)]
            if len(before) and len(after):
                if np.nanmax(before) - speed_norm[i] >= min_drop and np.nanmax(after) - speed_norm[i] >= min_drop:
                    if not valleys or i - valleys[-1] >= min_gap:
                        valleys.append(i)
                    elif speed_norm[i] < speed_norm[valleys[-1]]:
                        valleys[-1] = i

    return peaks, valleys


def find_velocity_gate(
    speed_norm: np.ndarray,
    peak_speed_i: int,
    dt: float,
    gate_pct: float,
) -> int:
    sustained = max(1, int(math.ceil((10.0 / 1000.0) / dt)))
    end = max(sustained + 1, peak_speed_i + 1)
    for i in range(0, max(1, end - sustained + 1)):
        window = speed_norm[i : i + sustained]
        if len(window) < sustained:
            break
        if np.nanmean(window) >= gate_pct:
            return i
    return max(0, peak_speed_i)


def detect_onset(time: np.ndarray, signal: np.ndarray, contact: float, config: OnsetConfig) -> float:
    valid = np.isfinite(time) & np.isfinite(signal)
    time = time[valid]
    signal = signal[valid]
    if len(time) < 8 or not np.isfinite(contact):
        return np.nan

    start = contact - config.search_back_s
    mask = (time >= start) & (time <= contact)
    if mask.sum() < 8:
        return np.nan
    t = time[mask]
    y = signal[mask]
    dt = median_dt(t)
    if not np.isfinite(dt) or dt <= 0:
        return np.nan

    y = smooth_signal(y, dt, config.smooth_ms)
    peak = np.nanmax(y)
    if not np.isfinite(peak) or peak <= 0:
        return np.nan

    peak_i = int(np.nanargmax(y))
    threshold = config.threshold_pct * peak
    sustained = max(1, int(math.ceil((config.sustained_ms / 1000.0) / dt)))

    search_y = y[: peak_i + 1]
    search_t = t[: peak_i + 1]
    non_forward = np.where(search_y <= 0)[0]
    start_i = int(non_forward[-1] + 1) if len(non_forward) else 0
    for i in range(start_i, max(start_i, len(search_y) - sustained + 1)):
        window = search_y[i : i + sustained]
        if np.all(window >= threshold) and np.nanmean(window) > 0:
            return float(search_t[i])
    return np.nan


def calculate_sequence_metrics(joint_velos: pd.DataFrame) -> pd.DataFrame:
    rows = []
    segment_cols = {
        "pelvis": ["pelvis_angular_velocity_x", "pelvis_angular_velocity_y", "pelvis_angular_velocity_z"],
        "torso": ["torso_angular_velocity_x", "torso_angular_velocity_y", "torso_angular_velocity_z"],
        "lead_hand": [
            "lead_hand_global_angular_velocity_x",
            "lead_hand_global_angular_velocity_y",
            "lead_hand_global_angular_velocity_z",
        ],
        "lead_elbow": [
            "lead_elbow_angular_velocity_x",
            "lead_elbow_angular_velocity_y",
            "lead_elbow_angular_velocity_z",
        ],
    }
    for sid, group in joint_velos.groupby("session_swing", sort=False):
        g = group.sort_values("time")
        contact = first_numeric(g["contact_time"])
        row: dict[str, float | str | int] = {"session_swing": sid}
        peak_order = []
        for segment, cols in segment_cols.items():
            if not set(cols).issubset(g.columns) or not np.isfinite(contact):
                continue
            t = g["time"].to_numpy(float)
            arr = g[cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
            mag = np.linalg.norm(arr, axis=1)
            mask = (t >= contact - 0.50) & (t <= contact) & np.isfinite(mag)
            if mask.sum() < 5:
                continue
            mt = t[mask]
            mm = mag[mask]
            idx = int(np.nanargmax(mm))
            row[f"{segment}_peak_time"] = mt[idx]
            row[f"{segment}_peak_ms_before_contact"] = (contact - mt[idx]) * 1000.0
            row[f"{segment}_peak_mag_deg_s"] = mm[idx]
            peak_order.append((mt[idx], segment))
        peak_order = sorted(peak_order)
        row["peak_order"] = ">".join(seg for _, seg in peak_order)
        row["peak_order_score"] = score_peak_order([seg for _, seg in peak_order])
        rows.append(row)
    return pd.DataFrame(rows)


def score_peak_order(order: list[str]) -> int:
    target = ["pelvis", "torso", "lead_elbow", "lead_hand"]
    positions = {seg: i for i, seg in enumerate(order)}
    score = 0
    for a, b in zip(target, target[1:]):
        if a in positions and b in positions and positions[a] < positions[b]:
            score += 1
    return score


def build_model_dataset(
    metadata: pd.DataFrame,
    poi: pd.DataFrame,
    hittrax: pd.DataFrame,
    manifest: pd.DataFrame,
    barrel: pd.DataFrame,
    onsets: pd.DataFrame,
    sequence: pd.DataFrame,
) -> pd.DataFrame:
    data = manifest[["session_swing", "user", "session", "hitter_side", "highest_playing_level", "event_order_valid", "analysis_event_valid", "has_hittrax", "has_force"]].copy()
    for frame in [metadata, poi, barrel, onsets, sequence]:
        keep = [c for c in frame.columns if c not in data.columns or c == "session_swing"]
        data = data.merge(frame[keep], on="session_swing", how="left")

    hit = hittrax.copy()
    hit["session_swing"] = hit["session_swing"].astype(str)
    hit = hit.add_prefix("hittrax_").rename(columns={"hittrax_session_swing": "session_swing"})
    data = data.merge(hit, on="session_swing", how="left")

    numeric_cols = [
        "composite_swing_time_ms",
        "initiation_spread_ms",
        "barrel_path_500ms_in",
        "barrel_path_from_onset_in",
        "barrel_path_final150ms_in",
        "bat_speed_mph_contact_x",
        "bat_speed_mph_max_x",
        "exit_velo_mph_x",
        "hittrax_pitch",
        "hittrax_vertical_distance",
        "hittrax_horizontal_distance",
        "hittrax_poi_x",
        "hittrax_poi_y",
        "hittrax_poi_z",
    ]
    for col in numeric_cols:
        if col in data:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    data["estimated_pitch_flight_time_ms"] = 40.0 / (65.0 * 1.4666667) * 1000.0
    data["estimated_composite_onset_after_release_ms"] = (
        data["estimated_pitch_flight_time_ms"] - data["composite_swing_time_ms"]
    )
    data["model_ready_primary"] = (
        data["analysis_event_valid"].fillna(False)
        & data["composite_swing_time_ms"].notna()
        & data["initiation_spread_ms"].notna()
        & data["barrel_path_from_onset_in"].notna()
    )
    data["manual_qc_exclude_reason"] = data["session_swing"].astype(str).map(MANUAL_QC_EXCLUSIONS).fillna("")
    data.loc[data["manual_qc_exclude_reason"].ne(""), "model_ready_primary"] = False
    return data


def build_qc_summary(
    manifest: pd.DataFrame, onsets: pd.DataFrame, model_dataset: pd.DataFrame
) -> pd.DataFrame:
    rows = [
        {"metric": "metadata_swings", "value": len(manifest)},
        {"metric": "analysis_event_valid", "value": int(manifest["analysis_event_valid"].sum())},
        {"metric": "strict_event_order_valid", "value": int(manifest["event_order_valid"].sum())},
        {"metric": "has_hittrax", "value": int(manifest["has_hittrax"].sum())},
        {"metric": "has_force", "value": int(manifest["has_force"].sum())},
        {"metric": "primary_model_ready", "value": int(model_dataset["model_ready_primary"].sum())},
        {
            "metric": "manual_qc_excluded",
            "value": int(model_dataset.get("manual_qc_exclude_reason", pd.Series(dtype=str)).astype(str).ne("").sum()),
        },
    ]
    if "onset_qc" in onsets:
        for key, val in onsets["onset_qc"].value_counts(dropna=False).items():
            rows.append({"metric": f"onset_qc_{key}", "value": int(val)})
    return pd.DataFrame(rows)


def fit_models(data: pd.DataFrame) -> dict[str, str]:
    out = {}
    d = data.loc[data["model_ready_primary"]].copy()
    cols = [
        "composite_swing_time_ms",
        "barrel_path_from_onset_in",
        "initiation_spread_ms",
        "bat_speed_mph_contact_x",
        "user",
    ]
    d = d[cols].dropna()
    if len(d) < 25 or d["user"].nunique() < 5:
        out["primary_mixed_model"] = "Not enough complete rows for mixed model."
        return out

    for col in ["barrel_path_from_onset_in", "initiation_spread_ms", "bat_speed_mph_contact_x"]:
        sd = d[col].std()
        d[f"z_{col}"] = (d[col] - d[col].mean()) / sd if sd else 0.0

    try:
        model = smf.mixedlm(
            "composite_swing_time_ms ~ z_barrel_path_from_onset_in + z_initiation_spread_ms + z_bat_speed_mph_contact_x",
            d,
            groups=d["user"],
        )
        fit = model.fit(reml=False, method="lbfgs", maxiter=200, disp=False)
        out["primary_mixed_model"] = fit.summary().as_text()
    except Exception as exc:
        out["primary_mixed_model"] = f"Mixed model failed: {type(exc).__name__}: {exc}"

    try:
        ols = smf.ols(
            "composite_swing_time_ms ~ z_barrel_path_from_onset_in + z_initiation_spread_ms + z_bat_speed_mph_contact_x + C(user)",
            d,
        ).fit()
        out["fixed_hitter_ols"] = ols.summary().as_text()
    except Exception as exc:
        out["fixed_hitter_ols"] = f"OLS model failed: {type(exc).__name__}: {exc}"
    return out


def make_figures(data: pd.DataFrame, figure_dir: Path) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    paths = []
    d = data.loc[data["model_ready_primary"]].copy()
    if d.empty:
        return paths

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(d["barrel_path_from_onset_in"], d["composite_swing_time_ms"], s=18, alpha=0.6)
    ax.set_xlabel("Barrel path from barrel onset to contact (in)")
    ax.set_ylabel("Composite swing time (ms)")
    ax.set_title("Composite Swing Time vs Barrel Path")
    path = figure_dir / "swing_time_vs_barrel_path.png"
    fig.tight_layout()
    path = save_figure(fig, path)
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(d["initiation_spread_ms"], d["composite_swing_time_ms"], s=18, alpha=0.6)
    ax.set_xlabel("Initiation spread (ms)")
    ax.set_ylabel("Composite swing time (ms)")
    ax.set_title("Composite Swing Time vs Segment-Onset Spread")
    path = figure_dir / "swing_time_vs_initiation_spread.png"
    fig.tight_layout()
    path = save_figure(fig, path)
    plt.close(fig)
    paths.append(path)

    top_users = d["user"].value_counts().head(12).index
    dd = d[d["user"].isin(top_users)].copy()
    if not dd.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        for user, group in dd.groupby("user"):
            ax.plot(
                group["barrel_path_from_onset_in"],
                group["composite_swing_time_ms"],
                marker="o",
                linestyle="",
                alpha=0.75,
                label=str(user),
            )
        ax.set_xlabel("Barrel path from barrel onset to contact (in)")
        ax.set_ylabel("Composite swing time (ms)")
        ax.set_title("Within-Hitter View: Top 12 Swing Counts")
        ax.legend(ncol=3, fontsize=8, frameon=False)
        path = figure_dir / "within_hitter_barrel_path_time.png"
        fig.tight_layout()
        path = save_figure(fig, path)
        plt.close(fig)
        paths.append(path)

    return paths


def save_figure(fig, path: Path) -> Path:
    try:
        fig.savefig(path, dpi=160)
        return path
    except OSError:
        unlocked_path = path.with_name(f"{path.stem}_updated{path.suffix}")
        fig.savefig(unlocked_path, dpi=160)
        print(f"Could not overwrite locked figure {path}; wrote {unlocked_path} instead.")
        return unlocked_path


def write_report(
    path: Path,
    data_root: Path,
    manifest: pd.DataFrame,
    onsets: pd.DataFrame,
    barrel: pd.DataFrame,
    model_dataset: pd.DataFrame,
    qc_summary: pd.DataFrame,
    model_summaries: dict[str, str],
    figure_paths: list[Path],
) -> None:
    ready = model_dataset.loc[model_dataset["model_ready_primary"]].copy()
    lines = [
        "# OBP Swing-Time Analysis Report",
        "",
        f"Data root: `{data_root}`",
        "",
        "## What This Measures",
        "",
        "This is a movement-time analysis, not a literal decision-time analysis. The primary clock starts at the earliest detected onset across pelvis, torso, and lead hand, then stops at OBP `contact_time`. Lead arm is still calculated as a reference/QC onset, but it is not part of the primary initiation clock.",
        "",
        "Primary formula:",
        "",
        "```text",
        "composite_swing_time_ms = (contact_time - composite_onset_time) * 1000",
        "initiation_spread_ms = (latest_primary_segment_onset - earliest_primary_segment_onset) * 1000",
        "```",
        "",
        "Because these swings were collected off a pitching machine set near 65 mph from about 40 ft, the results should be interpreted as controlled movement-time relationships, not real-pitcher deception or decision-quality effects.",
        "",
        "Primary onset definition: all primary segment onsets use 3D resultant angular velocity from OBP `joint_velos`. The detector smooths angular-velocity magnitude, finds the segment's pre-contact angular-velocity peak, then fits a continuous two-piece linear model from the start of the search window through that peak. That piecewise change point defines the ramp window. Pelvis onset is selected from local positive signed angular-acceleration peaks that reach at least 25% of the largest pelvis burst inside that ramp window; when multiple peaks qualify, the selected pelvis onset is the one closest to 191.7 ms before contact. Torso onset is the largest positive signed angular-acceleration burst inside its ramp window. Lead-hand onset uses an experimental hybrid hand-path rule. The search window starts at -200 ms before contact and normally stops just before the lead elbow crosses the back shoulder's x-plane; if the elbow crossing cannot be detected, the window ends at the lead-wrist crossing, and if that also fails it falls back to -100 ms. Within that window, swings with at least 2 cm of lead-hand load-back are marked at the first sustained forward lead-hand move after the load-back trough. Other swings are treated as drift-forward and marked at the first 15% linear x-acceleration jump opposite the early drift direction. Pelvis, torso, and lead hand define the primary clock; lead arm remains available for QC and sequencing context. Barrel onset is not included in the clock, but the barrel trace remains in the QC viewer.",
        "",
        "`contact_time` is treated as a provided OBP processed event. The public hitting README states that contact is included in the full-signal tables, but it does not document the exact contact-detection algorithm. In a related OBP swing visualizer, contact is estimated from peak reconstructed barrel speed, so contact-derived timing should be interpreted with that uncertainty in mind.",
        "",
        "## Dataset QC",
        "",
        qc_summary.to_markdown(index=False),
        "",
        "## Primary Metric Summary",
        "",
    ]
    if ready.empty:
        lines.append("No model-ready swings were available after QC.")
    else:
        summary_cols = [
            "composite_swing_time_ms",
            "initiation_spread_ms",
            "barrel_path_from_onset_in",
            "barrel_path_500ms_in",
            "barrel_path_final150ms_in",
            "bat_speed_mph_contact_x",
            "exit_velo_mph_x",
            "estimated_pitch_flight_time_ms",
            "estimated_composite_onset_after_release_ms",
        ]
        existing = [col for col in summary_cols if col in ready.columns]
        lines.append(
            ready[existing]
            .describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
            .round(2)
            .to_markdown()
        )
        lines.extend(["", "## Simple Relationships", ""])
        corr_cols = [
            "composite_swing_time_ms",
            "initiation_spread_ms",
            "barrel_path_from_onset_in",
            "barrel_path_500ms_in",
            "barrel_path_final150ms_in",
            "bat_speed_mph_contact_x",
            "exit_velo_mph_x",
            "estimated_composite_onset_after_release_ms",
        ]
        corr_cols = [c for c in corr_cols if c in ready.columns]
        lines.append(ready[corr_cols].corr(numeric_only=True).round(3).to_markdown())

    lines.extend(["", "## Figures", ""])
    if figure_paths:
        for fig in figure_paths:
            lines.append(f"- `{fig}`")
    else:
        lines.append("No figures generated.")

    lines.extend(["", "## Model Summaries", ""])
    for name, summary in model_summaries.items():
        lines.extend([f"### {name}", "", "```text", summary[:12000], "```", ""])

    lines.extend(
        [
            "## Interpretation Guardrails",
            "",
        "- Do not call `composite_onset_time` the exact conscious decision point.",
        "- `estimated_composite_onset_after_release_ms` is a machine-flight proxy from about 40 ft and pitch speed, not measured release timing.",
        "- Treat the primary onset definition as one operational definition and compare it with `sensitivity_onsets.csv` plus the QC viewer.",
            "- OBP's controlled machine setting reduces deception and pitch-variation questions; it strengthens mechanical repeatability questions.",
            "- The shortest barrel path should not automatically be treated as best without checking bat speed, contact point, and outcome data.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_table(df: pd.DataFrame, csv_path: Path, parquet: bool = True) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(csv_path, index=False)
    except PermissionError:
        unlocked_path = csv_path.with_name(f"{csv_path.stem}_updated{csv_path.suffix}")
        df.to_csv(unlocked_path, index=False)
        print(f"Could not overwrite locked file {csv_path}; wrote {unlocked_path} instead.")
        csv_path = unlocked_path
    if parquet:
        try:
            df.to_parquet(csv_path.with_suffix(".parquet"), index=False)
        except Exception:
            pass


def first_numeric(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    return float(vals.iloc[0]) if len(vals) else np.nan


def nearest_index(values: np.ndarray, target: float) -> int:
    return int(np.nanargmin(np.abs(values - target)))


def median_dt(time: np.ndarray) -> float:
    diffs = np.diff(time)
    diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
    return float(np.median(diffs)) if len(diffs) else np.nan


def smooth_signal(y: np.ndarray, dt: float, smooth_ms: float) -> np.ndarray:
    if len(y) < 7:
        return y
    window = max(5, int(round((smooth_ms / 1000.0) / dt)))
    if window % 2 == 0:
        window += 1
    window = min(window, len(y) if len(y) % 2 == 1 else len(y) - 1)
    if window < 5:
        return y
    return savgol_filter(y, window_length=window, polyorder=2, mode="interp")


def smooth_positions(xy: np.ndarray, dt: float, smooth_ms: float) -> np.ndarray:
    out = np.asarray(xy, dtype=float).copy()
    for col in range(out.shape[1]):
        out[:, col] = smooth_signal(out[:, col], dt, smooth_ms)
    return out


def normalize_positive(values: np.ndarray) -> np.ndarray:
    y = np.asarray(values, dtype=float)
    y = np.where(np.isfinite(y), y, 0.0)
    y = np.maximum(y, 0.0)
    peak = float(np.nanmax(y)) if len(y) else np.nan
    return y / peak if np.isfinite(peak) and peak > 0 else np.zeros_like(y)


def folded_angle_degrees(angle: np.ndarray) -> np.ndarray:
    return ((angle + 90.0) % 180.0) - 90.0


def axis_label(axes: tuple[int, int]) -> str:
    names = {0: "x", 1: "y", 2: "z"}
    return "".join(names.get(axis, "?") for axis in axes)


def has_landmark_xyz(df: pd.DataFrame, prefix: str) -> bool:
    return all(f"{prefix}_{axis}" in df.columns for axis in ["x", "y", "z"])


def landmark_xyz(df: pd.DataFrame, prefix: str) -> np.ndarray:
    cols = [f"{prefix}_{axis}" for axis in ["x", "y", "z"]]
    return df[cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)


def midpoint_landmark_xyz(df: pd.DataFrame, a_prefix: str, b_prefix: str) -> np.ndarray | None:
    if not has_landmark_xyz(df, a_prefix) or not has_landmark_xyz(df, b_prefix):
        return None
    return (landmark_xyz(df, a_prefix) + landmark_xyz(df, b_prefix)) / 2.0


def speed_from_positions(time: np.ndarray, xyz: np.ndarray) -> np.ndarray:
    if len(time) < 2:
        return np.full(len(time), np.nan)
    vx = np.gradient(xyz[:, 0], time)
    vy = np.gradient(xyz[:, 1], time)
    vz = np.gradient(xyz[:, 2], time)
    return np.sqrt(vx * vx + vy * vy + vz * vz)


def directional_velocity_to_contact(time: np.ndarray, xyz: np.ndarray, contact: float) -> np.ndarray:
    valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
    out = np.full(len(time), np.nan)
    if valid.sum() < 5 or not np.isfinite(contact):
        return out
    t = time[valid]
    p = xyz[valid]
    contact_i = nearest_index(t, contact)
    pre_i = max(0, np.searchsorted(t, contact - 0.100, side="left"))
    direction = p[contact_i] - p[pre_i]
    norm = np.linalg.norm(direction)
    if not np.isfinite(norm) or norm <= 0:
        return out
    unit = direction / norm
    vel = np.column_stack(
        [
            np.gradient(p[:, 0], t),
            np.gradient(p[:, 1], t),
            np.gradient(p[:, 2], t),
        ]
    )
    projected = vel @ unit
    out[np.where(valid)[0]] = projected
    return out


def path_length(xyz: np.ndarray) -> float:
    if len(xyz) < 2:
        return np.nan
    diffs = np.diff(xyz, axis=0)
    steps = np.sqrt(np.sum(diffs * diffs, axis=1))
    return float(np.nansum(steps))


def safe_div(a: float, b: float) -> float:
    if not np.isfinite(a) or not np.isfinite(b) or b == 0:
        return np.nan
    return a / b
