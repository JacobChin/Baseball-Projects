from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from analyze_attack_angle_zone import (  # noqa: E402
    attack_payload_for_frames,
    clean_float,
    make_velocity20_onset_row,
    set_attack_viewer_event_groups,
)
from create_swing_qc_viewer import build_payload  # noqa: E402
from obp_swing_time.pipeline import (  # noqa: E402
    expected_paths,
    read_csv,
    read_zipped_csv,
    validate_paths,
)


DEFAULT_DATA_ROOT = Path(r"E:\Baseball\Data\OBP")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Viewer-Payloads"
METRICS_PATH = PROJECT_ROOT / "outputs" / "attack_angle_zone_metrics.csv"
MANIFEST_PATH = PROJECT_ROOT / "outputs" / "swing_manifest.csv"
ONSETS_PATH = PROJECT_ROOT / "outputs" / "onset_metrics.csv"
VELOCITY20_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "initiation_analysis"
    / "velocity20_primary_model"
    / "velocity20_primary_onset_rows.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build compact interactive-viewer payloads for every model-ready OBP swing."
    )
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--session-swing", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def row_lookup(frame: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        str(row["session_swing"]): row
        for _, row in frame.drop_duplicates("session_swing", keep="last").iterrows()
    }


def group_lookup(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if frame.empty:
        return {}
    return {
        str(swing_id): group.copy()
        for swing_id, group in frame.groupby("session_swing", sort=False)
    }


def make_attack_payload(
    swing_id: str,
    metrics_row: pd.Series,
    landmarks: pd.DataFrame,
    joint_velos: pd.DataFrame,
    onset_row: pd.Series,
    manifest_row: pd.Series,
    metadata_row: pd.Series | None,
    velocity_row: pd.Series,
) -> dict:
    contact = float(manifest_row["contact_time"])
    viewer_onsets = make_velocity20_onset_row(onset_row, velocity_row, contact)
    payload = build_payload(
        swing_id,
        landmarks,
        viewer_onsets,
        manifest_row,
        metadata_row,
        joint_velos,
        0.55,
        0.10,
    )
    payload["sessionSwing"] = swing_id
    payload["attackAngle"] = attack_payload_for_frames(landmarks, payload, metrics_row)
    set_attack_viewer_event_groups(payload, velocity_row, contact)
    payload["tracers"] = [
        tracer
        for tracer in payload.get("tracers", [])
        if tracer.get("pointKey") != "back_elbow"
    ]
    payload["searchWindows"] = []
    payload["viewerOptions"] = {
        "displayTitle": swing_id,
        "subtitle": "",
        "hideMetrics": True,
        "hideSearchWindows": True,
        "hideAccelerationVectors": True,
        "hidePointLegend": True,
        "hidePointKeys": ["thorax_top", "thorax_bottom", "left_wrist", "right_wrist"],
        "singleLandmarkColor": "#95a5a6",
        "definitionHref": (
            "https://raw.githack.com/JacobChin/Baseball-Projects/main/"
            "OBP-Biomechanical-Swing-Viewer/docs/viewer_definitions.html"
        ),
        "noteText": (
            "Timeline marks show detected events. Red barrel ribbon marks the selected "
            "contact-relevant attack-angle segment."
        ),
        "methodologyNote": (
            "Contact bat speed and attack angle were recomputed frame-by-frame from marker "
            "data to build this viewer. Small differences from OBP contact fields were "
            "expected because OBP's processed contact metrics were not available across "
            "the full swing path."
        ),
    }

    keep_meta = [
        "user",
        "session",
        "hitter_side",
        "highest_playing_level",
        "session_height_in",
        "session_mass_lbs",
        "attack_angle_contact_x",
    ]
    payload["metadata"] = {
        key: payload.get("metadata", {}).get(key)
        for key in keep_meta
        if key in payload.get("metadata", {})
    }
    payload["contactMetrics"] = {
        "bat_speed": {
            "label": "Bat Speed",
            "value": clean_float(metrics_row.get("attack_angle_contact_bat_speed_mph")),
            "units": "mph",
        },
        "attack_angle": {
            "label": "Attack Angle",
            "value": clean_float(metrics_row.get("attack_angle_contact_computed_deg")),
            "units": "deg",
        },
        "attack_direction": {
            "label": "Attack Direction",
            "value": clean_float(metrics_row.get("attack_direction_contact_pull_deg")),
            "units": "deg",
        },
        "swing_length": {
            "label": "Swing Length",
            "value": clean_float(metrics_row.get("swing_length_lead_hand_onset_to_contact_ft")),
            "units": "ft",
        },
        "swing_path_tilt": {
            "label": "Swing Path Tilt",
            "value": clean_float(metrics_row.get("swing_path_tilt_contact_deg")),
            "units": "deg",
        },
        "contact_x_relative_com": {
            "label": "Out Front (Contact COM)",
            "value": clean_float(metrics_row.get("contact_barrel_x_relative_com_in")),
            "units": "in",
        },
        "contact_x_relative_preswing_com": {
            "label": "Out Front (Rear-most COM)",
            "value": clean_float(
                metrics_row.get("contact_barrel_x_relative_preswing_com_in")
            ),
            "units": "in",
        },
    }

    metric_keys = [
        "attack_zone_time_ms",
        "longest_attack_zone_ms",
        "attack_zone_pct_of_swing",
        "attack_zone_path_length_in",
        "attack_zone_path_pct",
        "attack_angle_contact_computed_deg",
        "attack_angle_contact_x",
        "attack_angle_contact_diff_deg",
        "attack_angle_contact_bat_speed_mph",
        "swing_length_lead_hand_onset_to_contact_in",
        "swing_length_lead_hand_onset_to_contact_ft",
        "swing_path_tilt_contact_deg",
        "contact_barrel_x_relative_com_in",
        "contact_barrel_x_relative_preswing_com_in",
        "contact_barrel_preswing_com_reference_ms_before_contact",
        "attack_angle_window_start_ms_before_contact",
        "attack_angle_speed_gate_pct",
        "attack_angle_speed_gate_mps",
        "attack_angle_max_window_speed_mps",
        "attack_angle_window_end_ms_after_contact",
        "attack_angle_window_end_ms_before_contact",
        "attack_angle_window_end_attack_direction_deg",
        "attack_angle_marker_time_offset_ms",
        "attack_zone_y_range_relative_com_in",
        "attack_zone_speed_mean_mph",
        "attack_zone_speed_max_mph",
        "attack_zone_speed_pct_max_mean",
        "attack_zone_speed_pct_max_peak",
        "attack_direction_contact_pull_deg",
        "attack_direction_zone_mean_pull_deg",
        "attack_direction_zone_median_pull_deg",
        "attack_direction_zone_range_deg",
    ]
    for key in metric_keys:
        if key in metrics_row:
            payload["metrics"][key] = clean_float(metrics_row.get(key))
    return payload


def write_payload(path: Path, payload: dict) -> int:
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":")).encode("utf-8")
    with path.open("wb") as raw_file:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            compresslevel=6,
            fileobj=raw_file,
            mtime=0,
        ) as compressed:
            compressed.write(encoded)
    return path.stat().st_size


def main() -> int:
    args = parse_args()
    paths = expected_paths(args.data_root)
    validate_paths(paths)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    metrics = pd.read_csv(METRICS_PATH)
    manifest = pd.read_csv(MANIFEST_PATH)
    onsets = pd.read_csv(ONSETS_PATH)
    velocity20 = pd.read_csv(VELOCITY20_PATH)
    metadata = read_csv(paths["metadata"])
    for frame in (metrics, manifest, onsets, velocity20, metadata):
        frame["session_swing"] = frame["session_swing"].astype(str)

    metrics = metrics.loc[metrics["model_ready_primary"].fillna(False).astype(bool)].copy()
    if args.session_swing:
        metrics = metrics.loc[metrics["session_swing"].eq(str(args.session_swing))]
    if args.limit is not None:
        metrics = metrics.head(args.limit)
    if metrics.empty:
        raise ValueError("No model-ready swings matched the requested selection.")

    selected = set(metrics["session_swing"])
    print(f"Loading signal data for {len(selected)} swings...")
    landmarks = read_zipped_csv(paths["landmarks"], selected)
    joint_velos = read_zipped_csv(paths["joint_velos"], selected, required=False)
    landmarks["session_swing"] = landmarks["session_swing"].astype(str)
    if not joint_velos.empty:
        joint_velos["session_swing"] = joint_velos["session_swing"].astype(str)

    landmark_groups = group_lookup(landmarks)
    velocity_groups = group_lookup(joint_velos)
    manifest_rows = row_lookup(manifest)
    onset_rows = row_lookup(onsets)
    metadata_rows = row_lookup(metadata)
    velocity_rows = row_lookup(velocity20)

    output_rows = []
    errors = []
    total = len(metrics)
    for number, (_, metrics_row) in enumerate(metrics.iterrows(), start=1):
        swing_id = str(metrics_row["session_swing"])
        output_path = args.output_dir / f"{swing_id}.json.gz"
        if output_path.exists() and not args.overwrite:
            output_rows.append(
                {
                    "session_swing": swing_id,
                    "payload_file": output_path.name,
                    "compressed_bytes": output_path.stat().st_size,
                    "status": "existing",
                }
            )
            continue
        try:
            payload = make_attack_payload(
                swing_id,
                metrics_row,
                landmark_groups[swing_id],
                velocity_groups.get(swing_id, pd.DataFrame()),
                onset_rows[swing_id],
                manifest_rows[swing_id],
                metadata_rows.get(swing_id),
                velocity_rows[swing_id],
            )
            size = write_payload(output_path, payload)
            output_rows.append(
                {
                    "session_swing": swing_id,
                    "payload_file": output_path.name,
                    "compressed_bytes": size,
                    "status": "written",
                }
            )
        except Exception as exc:
            errors.append({"session_swing": swing_id, "error": repr(exc)})
        if number % 25 == 0 or number == total:
            print(f"Processed {number}/{total}; errors={len(errors)}")

    output_frame = pd.DataFrame(output_rows)
    output_frame.to_csv(args.output_dir / "payload_manifest.csv", index=False)
    if errors:
        error_frame = pd.DataFrame(errors)
        error_frame.to_csv(args.output_dir / "payload_errors.csv", index=False)
        raise RuntimeError(
            f"Payload generation failed for {len(errors)} swings. "
            f"See {args.output_dir / 'payload_errors.csv'}."
        )

    total_bytes = int(output_frame["compressed_bytes"].sum())
    print(
        f"Wrote {len(output_frame)} payloads totaling "
        f"{total_bytes / 1024 / 1024:.1f} MiB to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
