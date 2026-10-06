from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from obp_swing_time.pipeline import (
    PRIMARY_CONFIG,
    expected_paths,
    median_dt,
    read_csv,
    read_zipped_csv,
    smooth_positions,
    validate_paths,
)


POINT_DEFS = [
    ("barrel", "barrel", "sweet_spot", "#d7263d"),
    ("handle proxy", "handle_proxy", "blast_hand", "#1b998b"),
    ("left hand", "left_hand", "lhjc", "#2e86de"),
    ("right hand", "right_hand", "rhjc", "#2e86de"),
    ("left wrist", "left_wrist", "lwjc", "#3498db"),
    ("right wrist", "right_wrist", "rwjc", "#3498db"),
    ("left elbow", "left_elbow", "lejc", "#8854d0"),
    ("right elbow", "right_elbow", "rejc", "#8854d0"),
    ("left shoulder", "left_shoulder", "lsjc", "#34495e"),
    ("right shoulder", "right_shoulder", "rsjc", "#34495e"),
    ("left hip", "left_hip", "left_hip", "#7f8c8d"),
    ("right hip", "right_hip", "right_hip", "#95a5a6"),
    ("left knee", "left_knee", "lkjc", "#6b7280"),
    ("right knee", "right_knee", "rkjc", "#6b7280"),
    ("left ankle", "left_ankle", "lajc", "#4b5563"),
    ("right ankle", "right_ankle", "rajc", "#4b5563"),
    ("thorax top", "thorax_top", "thorax_prox", "#111827"),
    ("thorax bottom", "thorax_bottom", "thorax_dist", "#111827"),
    ("thorax", "thorax", "thorax_ap", "#111827"),
    ("center mass", "center_mass", "centerofmass", "#f39c12"),
]


STICK_SEGMENTS = [
    ("left_shoulder", "right_shoulder", "#243b53", 5),
    ("left_hip", "right_hip", "#52616b", 5),
    ("left_shoulder", "left_hip", "#52616b", 4),
    ("right_shoulder", "right_hip", "#52616b", 4),
    ("thorax_top", "thorax_bottom", "#111827", 3),
    ("left_shoulder", "left_elbow", "#5f6caf", 5),
    ("left_elbow", "left_hand", "#5f6caf", 5),
    ("right_shoulder", "right_elbow", "#5f6caf", 5),
    ("right_elbow", "right_hand", "#5f6caf", 5),
    ("left_hip", "left_knee", "#52616b", 5),
    ("left_knee", "left_ankle", "#52616b", 5),
    ("right_hip", "right_knee", "#52616b", 5),
    ("right_knee", "right_ankle", "#52616b", 5),
    ("handle_proxy", "barrel", "#d7263d", 7),
]


EVENT_COLORS = {
    "pelvis_onset_time": "#8e44ad",
    "torso_onset_time": "#2980b9",
    "lead_arm_onset_time": "#6c5ce7",
    "lead_hand_onset_time": "#0984e3",
    "fp10_time": "#f59e0b",
    "fp100_time": "#ea580c",
    "force_climb_start_time": "#16a34a",
    "lead_force_max_time": "#dc2626",
    "contact_time": "#111111",
}


TRACE_DEFS = [
    ("pelvis", "pelvis", "pelvis_onset_time", EVENT_COLORS["pelvis_onset_time"]),
    ("torso", "torso", "torso_onset_time", EVENT_COLORS["torso_onset_time"]),
    ("lead arm", "lead_arm", "lead_arm_onset_time", EVENT_COLORS["lead_arm_onset_time"]),
    ("lead hand", "lead_hand", "lead_hand_onset_time", EVENT_COLORS["lead_hand_onset_time"]),
    ("back elbow", "back_elbow", None, "#a855f7"),
    ("center mass", "center_mass", None, "#f39c12"),
    ("barrel", "barrel", None, "#c0392b"),
]

TRACE_AXES = {
    "pelvis": ("front", (1, 2), "y/z"),
    "torso": ("top", (0, 1), "x/y"),
    "lead_arm": ("top", (0, 1), "x/y"),
    "lead_hand": ("top", (0, 1), "x/y"),
    "back_elbow": ("top", (0, 1), "x/y"),
    "center_mass": ("top", (0, 1), "x/y"),
    "barrel": ("top", (0, 1), "x/y"),
}

TRACE_GATE_PCT = {
    "pelvis": None,
    "torso": None,
    "lead_arm": None,
    "lead_hand": None,
    "back_elbow": None,
    "center_mass": None,
    "barrel": None,
}

TRACE_PERCENT_WINDOW_MS = (-350.0, -50.0)
TRACE_PERCENT_WINDOW_OVERRIDES_MS = {
    "lead_hand": (-200.0, -100.0),
}


ANGULAR_VELOCITY_COLS = {
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
    "back_elbow": [
        "rear_elbow_angular_velocity_x",
        "rear_elbow_angular_velocity_y",
        "rear_elbow_angular_velocity_z",
    ],
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a frame-by-frame OBP swing QC viewer.")
    parser.add_argument("--data-root", default=r"E:\Baseball\Data\OBP")
    parser.add_argument("--session-swing", default=None, help="Example: 103_1")
    parser.add_argument("--output", default=None, help="Output HTML path.")
    parser.add_argument("--window-before", type=float, default=0.55)
    parser.add_argument("--window-after", type=float, default=0.08)
    args = parser.parse_args(argv)

    data_root = Path(args.data_root)
    paths = expected_paths(data_root)
    validate_paths(paths)

    onset_path = PROJECT_ROOT / "outputs" / "onset_metrics.csv"
    manifest_path = PROJECT_ROOT / "outputs" / "swing_manifest.csv"
    if not onset_path.exists() or not manifest_path.exists():
        raise FileNotFoundError(
            "Run `py scripts\\run_obp_swing_time.py` first so onset metrics exist."
        )

    onsets = pd.read_csv(onset_path)
    manifest = pd.read_csv(manifest_path)
    metadata = read_csv(paths["metadata"])

    session_swing = args.session_swing or choose_default_swing(onsets)
    selected = {str(session_swing)}
    landmarks = read_zipped_csv(paths["landmarks"], selected)
    if landmarks.empty:
        raise ValueError(f"Swing not found in landmarks: {session_swing}")
    joint_velos = read_zipped_csv(paths["joint_velos"], selected, required=False)

    swing_onsets = onsets.loc[onsets["session_swing"].astype(str) == str(session_swing)]
    swing_manifest = manifest.loc[manifest["session_swing"].astype(str) == str(session_swing)]
    swing_metadata = metadata.loc[metadata["session_swing"].astype(str) == str(session_swing)]
    if swing_onsets.empty:
        raise ValueError(f"Swing not found in onset metrics: {session_swing}")

    payload = build_payload(
        str(session_swing),
        landmarks,
        swing_onsets.iloc[0],
        swing_manifest.iloc[0] if not swing_manifest.empty else None,
        swing_metadata.iloc[0] if not swing_metadata.empty else None,
        joint_velos,
        args.window_before,
        args.window_after,
    )

    output = Path(args.output) if args.output else PROJECT_ROOT / "outputs" / "qc_viewers" / f"{session_swing}.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(payload), encoding="utf-8")
    print(output)
    return 0


def choose_default_swing(onsets: pd.DataFrame) -> str:
    ready = onsets.loc[onsets["onset_qc"].eq("ok")].copy()
    if ready.empty:
        ready = onsets.copy()
    ready["rank_target"] = (
        pd.to_numeric(ready["composite_swing_time_ms"], errors="coerce").sub(225).abs()
        + pd.to_numeric(ready.get("lead_hand_to_contact_ms"), errors="coerce").sub(150).abs()
    )
    return str(ready.sort_values("rank_target").iloc[0]["session_swing"])


def build_payload(
    session_swing: str,
    landmarks: pd.DataFrame,
    onsets: pd.Series,
    manifest: pd.Series | None,
    metadata: pd.Series | None,
    joint_velos: pd.DataFrame,
    window_before: float,
    window_after: float,
) -> dict:
    g = landmarks.sort_values("time").copy()
    for col in g.columns:
        if col != "session_swing":
            g[col] = pd.to_numeric(g[col], errors="coerce")

    contact_time = float(onsets.get("contact_time", np.nan))
    if not np.isfinite(contact_time):
        contact_time = first_valid(g["contact_time"])
    start = contact_time - window_before
    end = contact_time + window_after
    g = g.loc[(g["time"] >= start) & (g["time"] <= end)].copy()
    if g.empty:
        raise ValueError("No frames found inside requested viewing window.")

    side = str(metadata.get("hitter_side", "") if metadata is not None else "").upper()

    frames = []
    point_names_for_bounds = []
    for _, _, source_prefix, _ in POINT_DEFS:
        if has_xyz(g, source_prefix):
            point_names_for_bounds.append(source_prefix)

    path_points = extract_points(g, "sweet_spot")

    for _, row in g.iterrows():
        points = {}
        for label, key, source_prefix, color in POINT_DEFS:
            if has_xyz(g, source_prefix):
                points[key] = {
                    "label": label,
                    "key": key,
                    "color": color,
                    "draw": True,
                    "xyz": [
                        clean_float(row[f"{source_prefix}_x"]),
                        clean_float(row[f"{source_prefix}_y"]),
                        clean_float(row[f"{source_prefix}_z"]),
                    ],
                }
        add_virtual_trace_points(points, side)
        frames.append(
            {
                "time": clean_float(row["time"]),
                "relativeMs": clean_float((row["time"] - contact_time) * 1000.0),
                "points": points,
            }
        )
    bounds = calculate_bounds(g, point_names_for_bounds)

    events = []
    for col, color in EVENT_COLORS.items():
        if col == "contact_time":
            value = contact_time
            label = "contact"
        elif col == "fp10_time":
            value = np.nan
            if manifest is not None:
                value = pd.to_numeric(pd.Series([manifest.get("fp_10_time")]), errors="coerce").iloc[0]
            if not np.isfinite(value) and "fp_10_time" in g:
                value = first_valid(g["fp_10_time"])
            label = "fp10"
        elif col == "fp100_time":
            value = np.nan
            if manifest is not None:
                value = pd.to_numeric(pd.Series([manifest.get("fp_100_time")]), errors="coerce").iloc[0]
            if not np.isfinite(value) and "fp_100_time" in g:
                value = first_valid(g["fp_100_time"])
            label = "fp100"
        elif col == "force_climb_start_time":
            value = np.nan
            if manifest is not None:
                value = pd.to_numeric(pd.Series([manifest.get("force_climb_start_time")]), errors="coerce").iloc[0]
            if not np.isfinite(value) and "force_climb_start_time" in g:
                value = first_valid(g["force_climb_start_time"])
            label = "force climb start"
        elif col == "lead_force_max_time":
            value = np.nan
            if manifest is not None:
                value = pd.to_numeric(pd.Series([manifest.get("lead_force_max_time")]), errors="coerce").iloc[0]
            if not np.isfinite(value) and "lead_force_max_time" in g:
                value = first_valid(g["lead_force_max_time"])
            label = "peak force"
        else:
            value = pd.to_numeric(pd.Series([onsets.get(col)]), errors="coerce").iloc[0]
            label = col.replace("_onset_time", " onset").replace("_", " ")
        if np.isfinite(value):
            idx = nearest_frame(frames, float(value))
            events.append(
                {
                    "name": label,
                    "time": clean_float(value),
                    "relativeMs": clean_float((value - contact_time) * 1000.0),
                    "frame": idx,
                    "color": color,
                }
            )

    metric_keys = [
        "composite_swing_time_ms",
        "initiation_spread_ms",
        "pelvis_to_contact_ms",
        "torso_to_contact_ms",
        "lead_arm_to_contact_ms",
        "lead_hand_to_contact_ms",
    ]
    metrics = {key: clean_float(onsets.get(key)) for key in metric_keys if key in onsets}
    if manifest is not None:
        for key in [
            "force_climb_start_to_contact_ms",
            "force_climb_start_to_fp100_ms",
            "force_climb_local_min_count",
            "force_climb_start_force_pct_bw",
            "lead_force_abs_max_pct_bw",
            "lead_force_abs_max_to_contact_ms",
            "lead_force_signed_at_abs_max_pct_bw",
            "lead_force_precontact_abs_max_pct_bw",
            "lead_force_precontact_abs_max_to_contact_ms",
            "lead_force_precontact_min_pct_bw",
            "lead_force_precontact_max_pct_bw",
            "lead_force_precontact_range_pct_bw",
            "lead_force_precontact_corrected_max_pct_bw",
            "lead_force_corrected_max_pct_bw",
            "lead_force_max_to_contact_ms",
        ]:
            if key in manifest:
                metrics[key] = clean_float(manifest.get(key))

    meta = {}
    if metadata is not None:
        for key in [
            "user",
            "session",
            "hitter_side",
            "highest_playing_level",
            "session_height_in",
            "session_mass_lbs",
            "blast_bat_speed_mph_x",
            "exit_velo_mph_x",
        ]:
            if key in metadata:
                meta[key] = clean_value(metadata[key])
    if manifest is not None:
        for key in [
            "event_order_valid",
            "has_hittrax",
            "has_force",
            "fp10_to_contact_ms",
            "fp100_to_contact_ms",
            "force_climb_start_to_contact_ms",
            "force_climb_start_to_fp100_ms",
            "force_climb_start_source",
            "force_climb_local_min_count",
            "force_climb_start_force_pct_bw",
            "lead_force_abs_max_pct_bw",
            "lead_force_abs_max_to_contact_ms",
            "lead_force_signed_at_abs_max_pct_bw",
            "lead_force_precontact_abs_max_pct_bw",
            "lead_force_precontact_abs_max_to_contact_ms",
            "lead_force_precontact_min_pct_bw",
            "lead_force_precontact_max_pct_bw",
            "lead_force_precontact_range_pct_bw",
            "lead_force_precontact_corrected_max_pct_bw",
            "lead_force_corrected_max_pct_bw",
            "lead_force_max_to_contact_ms",
            "force_qc_exclude",
            "force_qc_note",
            "force_peak_note",
        ]:
            if key in manifest:
                meta[key] = clean_value(manifest[key])

    return {
        "sessionSwing": session_swing,
        "hitterSide": side,
        "contactTime": contact_time,
        "frames": frames,
        "events": sorted(events, key=lambda e: e["time"]),
        "searchWindows": build_search_windows(onsets, frames, contact_time),
        "tracers": build_tracers(onsets, frames),
        "inflectionMarkers": build_inflection_markers(onsets, frames),
        "velocities": build_velocity_series(frames, contact_time, joint_velos, build_trace_percent_windows(onsets)),
        "metrics": metrics,
        "metadata": meta,
        "bounds": bounds,
        "barrelPath": path_points,
        "stickSegments": [
            {"a": a, "b": b, "color": color, "width": width}
            for a, b, color, width in STICK_SEGMENTS
        ],
    }


def build_search_windows(onsets: pd.Series, frames: list[dict], contact_time: float) -> list[dict]:
    start = pd.to_numeric(pd.Series([onsets.get("lead_hand_search_window_start_time")]), errors="coerce").iloc[0]
    end = pd.to_numeric(pd.Series([onsets.get("lead_hand_search_window_end_time")]), errors="coerce").iloc[0]
    if not np.isfinite(start) or not np.isfinite(end):
        return []
    source = clean_value(onsets.get("lead_hand_search_window_end_source", ""))
    return [
        {
            "label": "lead hand/back elbow/barrel",
            "description": "Lead-hand, back-elbow, and barrel acceleration percent range, ending at lead-elbow back-shoulder x-plane crossing when available, otherwise lead-wrist crossing.",
            "source": source,
            "startTime": clean_float(float(start)),
            "endTime": clean_float(float(end)),
            "startRelativeMs": clean_float((float(start) - contact_time) * 1000.0),
            "endRelativeMs": clean_float((float(end) - contact_time) * 1000.0),
            "startFrame": nearest_frame(frames, float(start)),
            "endFrame": nearest_frame(frames, float(end)),
            "startFrameRelativeMs": clean_float(frames[nearest_frame(frames, float(start))]["relativeMs"]),
            "endFrameRelativeMs": clean_float(frames[nearest_frame(frames, float(end))]["relativeMs"]),
            "color": EVENT_COLORS["lead_hand_onset_time"],
        }
    ]


def build_trace_percent_windows(onsets: pd.Series) -> dict[str, tuple[float, float]]:
    start = pd.to_numeric(pd.Series([onsets.get("lead_hand_search_window_start_time")]), errors="coerce").iloc[0]
    end = pd.to_numeric(pd.Series([onsets.get("lead_hand_search_window_end_time")]), errors="coerce").iloc[0]
    if not np.isfinite(start) or not np.isfinite(end):
        return {}
    window = tuple(sorted((float(start), float(end))))
    return {
        "lead_hand": window,
        "back_elbow": window,
        "barrel": window,
    }


def render_html(payload: dict) -> str:
    data = json.dumps(payload, allow_nan=False)
    title = f"Swing QC Viewer - {payload['sessionSwing']}"
    viewer_options = payload.get("viewerOptions", {})
    search_window_div = '' if viewer_options.get("hideSearchWindows") else '<div class="trace-controls" id="searchWindows"></div>'
    metrics_section = '' if viewer_options.get("hideMetrics") else '<h2>Key Metrics</h2>\n      <table id="metrics"></table>'
    definition_href = viewer_options.get("definitionHref")
    definition_link = f'<a class="definitions-link" href="{html.escape(str(definition_href))}" target="_blank">Definitions</a>' if definition_href else ''
    note_text = viewer_options.get(
        "noteText",
        "Timeline marks show detected events. Traces begin at the first displayed frame and draw forward to the current frame. A translucent red ribbon outside the barrel marks frames where attack angle is in the 5-20 degree ideal window; the barrel trace readout includes timing-corrected sweet-spot speed in mph."
    )
    methodology_note = viewer_options.get(
        "methodologyNote",
        "Contact bat speed and attack angle were recomputed frame-by-frame from marker data to build this viewer. Small differences from OBP contact fields were expected because OBP's processed contact metrics were not available across the full swing path."
    )
    display_title = viewer_options.get("displayTitle", payload["sessionSwing"])
    subtitle = viewer_options.get("subtitle", "Scrub frame by frame to verify whether detected onsets and contact look intuitive.")
    subtitle_html = f'<p class="sub">{html.escape(subtitle)}</p>' if subtitle else ''
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #f5f7fa;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #64748b;
      --line: #d8dee9;
      --accent: #0f766e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    }}
    main {{
      width: min(1480px, calc(100% - 32px));
      margin: 24px auto 40px;
    }}
    header {{
      display: flex;
      gap: 16px;
      align-items: end;
      justify-content: space-between;
      margin-bottom: 16px;
    }}
    h1 {{ margin: 0; font-size: 28px; }}
    .sub {{ color: var(--muted); margin: 4px 0 0; }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) 360px;
      gap: 16px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .views {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    canvas {{
      width: 100%;
      aspect-ratio: 1.05;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfdff;
      display: block;
    }}
    h2 {{
      margin: 0 0 10px;
      font-size: 17px;
    }}
    .controls {{
      display: grid;
      grid-template-columns: auto auto auto 1fr auto;
      gap: 10px;
      align-items: center;
      margin-top: 12px;
    }}
    button {{
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      padding: 7px 10px;
      cursor: pointer;
    }}
    button:hover {{ border-color: var(--accent); }}
    input[type=range] {{ width: 100%; }}
    .time {{
      font-variant-numeric: tabular-nums;
      color: var(--muted);
      white-space: nowrap;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 16px;
      font-size: 13px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 6px 4px;
      text-align: left;
      vertical-align: top;
    }}
    td:last-child, th:last-child {{ text-align: right; }}
    .event-list td:first-child {{
      font-weight: 600;
    }}
    .event-group td {{
      padding-top: 12px;
      color: #52637a;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border-bottom: 0;
    }}
    .swatch {{
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 6px;
      vertical-align: -1px;
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 12px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
    }}
    .trace-controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 14px;
      align-items: center;
      margin-top: 12px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfdff;
      font-size: 13px;
    }}
    .trace-controls strong {{
      margin-right: 2px;
    }}
    .trace-controls label {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      white-space: nowrap;
      cursor: pointer;
    }}
    .trace-controls input {{
      margin: 0;
    }}
    .velocity-readout {{
      color: var(--muted);
      font-variant-numeric: tabular-nums;
      font-size: 12px;
    }}
    .note {{
      color: var(--muted);
      font-size: 13px;
      margin: 10px 0 0;
    }}
    .viewer-footer {{
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(240px, 0.85fr);
      gap: 16px;
      align-items: start;
      margin-top: 10px;
    }}
    .footer-left {{
      min-height: 240px;
      display: flex;
      flex-direction: column;
    }}
    .viewer-tools {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 12px;
      align-items: center;
      color: var(--muted);
      font-size: 13px;
    }}
    .zone-controls {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .zone-controls input {{
      width: 58px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 5px 6px;
      font: inherit;
    }}
    .definitions-link {{
      color: #1d4ed8;
      text-decoration: none;
      font-weight: 600;
    }}
    .definitions-link:hover {{ text-decoration: underline; }}
    .zone-summary {{
      color: var(--ink);
      font-size: 13px;
      margin-top: 8px;
      font-variant-numeric: tabular-nums;
    }}
    .zone-summary div {{ margin-top: 3px; }}
    .viewer-explain, .event-note {{
      margin-top: 10px;
      padding-top: 0;
    }}
    .viewer-explain .note, .event-note .note {{ margin-top: 0; }}
    .definitions-note, .methodology-note {{
      color: var(--muted);
      font-size: 13px;
      margin: 8px 0 0;
    }}
    .inline-metadata h2 {{
      margin-top: 0;
    }}
    .inline-metadata table {{
      margin-bottom: 0;
    }}
    .contact-metrics-inline {{
      margin-top: 10px;
      max-width: 420px;
    }}
    .contact-metrics-heading {{
      margin: 8px 0 3px;
      font-size: 14px;
    }}
    .contact-metrics-inline table {{
      margin-bottom: 0;
      font-size: 12px;
    }}
    .contact-metrics-inline td {{
      padding: 4px 0;
    }}
    @media (max-width: 980px) {{
      .viewer-footer {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 980px) {{
      .grid, .views {{ grid-template-columns: 1fr; }}
      header {{ display: block; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Swing QC Viewer: {html.escape(display_title)}</h1>
      {subtitle_html}
    </div>
    <div class="time" id="frameLabel"></div>
  </header>

  <section class="grid">
    <div class="panel">
      <div class="views">
        <div>
          <h2>Side View: x vs z</h2>
          <canvas id="side"></canvas>
        </div>
        <div>
          <h2>Top View: x vs y</h2>
          <canvas id="top"></canvas>
        </div>
        <div>
          <h2>Front View: y vs z</h2>
          <canvas id="front"></canvas>
        </div>
      </div>
      <div class="controls">
        <button id="back">Prev</button>
        <button id="play">Play</button>
        <button id="forward">Next</button>
        <input id="slider" type="range" min="0" max="0" value="0">
        <span class="time" id="timeText"></span>
      </div>
      <div class="trace-controls" id="traceControls"></div>
      {search_window_div}
      <div class="legend" id="legend"></div>
      <div class="viewer-footer">
        <div class="footer-left">
          <div class="viewer-tools">
            <label class="zone-controls">Ideal AA
              <input id="idealMin" type="number" step="1" value="5">
              <span>to</span>
              <input id="idealMax" type="number" step="1" value="20">
              <span>deg</span>
            </label>
          </div>
          <div class="zone-summary" id="zoneSummary"></div>
          <div class="contact-metrics-inline">
            <h2 class="contact-metrics-heading">Contact Metrics</h2>
            <table id="contactMetrics"></table>
          </div>
        </div>
        <div class="inline-metadata">
          <h2>Hitter Info</h2>
          <table id="metadata"></table>
          <p class="methodology-note">{html.escape(methodology_note)}</p>
        </div>
      </div>
    </div>

    <aside class="panel">
      <h2>Event Times</h2>
      <table class="event-list" id="events"></table>
      <div class="event-note">
        <p class="note">{html.escape(note_text)}</p>
        <p class="definitions-note">Definitions of key metrics: {definition_link}</p>
      </div>
      {metrics_section}
    </aside>
  </section>
</main>

<script>
const payload = {data};
let frameIndex = 0;
let playing = false;
let timer = null;

const side = document.getElementById("side");
const topCanvas = document.getElementById("top");
const front = document.getElementById("front");
const slider = document.getElementById("slider");
const play = document.getElementById("play");
const traceState = Object.fromEntries(payload.tracers.map(tracer => [tracer.pointKey, Boolean(tracer.defaultOn)]));
let activeIdealMin = Number(payload.attackAngle?.idealMinDeg ?? 5);
let activeIdealMax = Number(payload.attackAngle?.idealMaxDeg ?? 20);
let activeAttackZoneFlags = [];
slider.max = payload.frames.length - 1;

function resizeCanvas(canvas) {{
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return [ctx, rect.width, rect.height];
}}

const AXES = {{
  side: [{{idx: 0, key: "x", flipLefty: true}}, {{idx: 2, key: "z"}}],
  top: [{{idx: 0, key: "x"}}, {{idx: 1, key: "y"}}],
  front: [{{idx: 1, key: "y"}}, {{idx: 2, key: "z"}}],
}};

function axisValue(point, axis) {{
  const raw = point[axis.idx];
  if (axis.flipLefty && payload.hitterSide === "L") {{
    const b = payload.bounds[axis.key];
    return b.max - (raw - b.min);
  }}
  return raw;
}}

function scalePoint(point, axes, width, height) {{
  const pad = 34;
  const b = payload.bounds;
  const xVal = axisValue(point, axes[0]);
  const yVal = axisValue(point, axes[1]);
  const xMin = b[axes[0].key].min;
  const xMax = b[axes[0].key].max;
  const yMin = b[axes[1].key].min;
  const yMax = b[axes[1].key].max;
  const x = pad + (xVal - xMin) / Math.max(0.001, xMax - xMin) * (width - pad * 2);
  const y = height - pad - (yVal - yMin) / Math.max(0.001, yMax - yMin) * (height - pad * 2);
  return [x, y];
}}
function drawFloorLine(ctx, axes, width, height) {{
  if (axes[1].key !== "z") return;
  const b = payload.bounds;
  const p1 = [0, 0, 0];
  const p2 = [0, 0, 0];
  p1[axes[0].idx] = b[axes[0].key].min;
  p2[axes[0].idx] = b[axes[0].key].max;
  const [x1, y1] = scalePoint(p1, axes, width, height);
  const [x2, y2] = scalePoint(p2, axes, width, height);
  ctx.save();
  ctx.strokeStyle = "#94a3b8";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = "#64748b";
  ctx.font = "11px Segoe UI, sans-serif";
  ctx.fillText("floor z=0", Math.min(x1, x2) + 6, y1 - 5);
  ctx.restore();
}}

function drawSegment(ctx, points, segment, axes, width, height) {{
  const hidden = payload.viewerOptions?.hidePointKeys || [];
  if (hidden.includes(segment.a) || hidden.includes(segment.b)) return;
  const a = points[segment.a]?.xyz;
  const b = points[segment.b]?.xyz;
  if (!a || !b || a.some(v => v === null) || b.some(v => v === null)) return;
  const [x1, y1] = scalePoint(a, axes, width, height);
  const [x2, y2] = scalePoint(b, axes, width, height);
  ctx.strokeStyle = segment.color;
  ctx.lineWidth = segment.width;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}}

function drawTrace(ctx, tracer, axes, width, height) {{
  if (!traceState[tracer.pointKey]) return;
  const end = Math.min(frameIndex, payload.frames.length - 1);
  const start = Math.min(tracer.startFrame, end);
  if (end < tracer.startFrame) return;
  ctx.strokeStyle = tracer.color;
  ctx.lineWidth = tracer.pointKey === "barrel" ? 3 : 2;
  ctx.globalAlpha = tracer.pointKey === "barrel" ? 0.55 : 0.6;
  ctx.lineCap = "round";
  ctx.beginPath();
  let started = false;
  for (let i = start; i <= end; i++) {{
    const p = payload.frames[i].points[tracer.pointKey]?.xyz;
    if (!p || p.some(v => v === null)) {{
      started = false;
      continue;
    }}
    const [x, y] = scalePoint(p, axes, width, height);
    if (!started) {{
      ctx.moveTo(x, y);
      started = true;
    }} else {{
      ctx.lineTo(x, y);
    }}
  }}
  ctx.stroke();
  ctx.globalAlpha = 1;
}}

function projectedTracePoint(frameIdx, pointKey, axes, width, height) {{
  const p = payload.frames[frameIdx]?.points?.[pointKey]?.xyz;
  if (!p || p.some(v => v === null)) return null;
  const [x, y] = scalePoint(p, axes, width, height);
  return {{x, y}};
}}

function median(values) {{
  const nums = values.filter(v => Number.isFinite(v)).sort((a, b) => a - b);
  if (!nums.length) return NaN;
  const mid = Math.floor(nums.length / 2);
  return nums.length % 2 ? nums[mid] : (nums[mid - 1] + nums[mid]) / 2;
}}

function medianFrameMs() {{
  const diffs = [];
  for (let i = 1; i < payload.frames.length; i++) {{
    const a = Number(payload.frames[i - 1]?.time);
    const b = Number(payload.frames[i]?.time);
    if (Number.isFinite(a) && Number.isFinite(b)) diffs.push((b - a) * 1000);
  }}
  return Math.abs(median(diffs));
}}

function rawAttackZoneFlag(sample) {{
  const aa = Number(sample?.attackAngleDeg);
  return Boolean(
    sample?.inSwingWindow &&
    sample?.passesSpeedGate &&
    sample?.passesDirectionGate &&
    Number.isFinite(aa) &&
    aa >= activeIdealMin &&
    aa <= activeIdealMax
  );
}}

function recalculateAttackZoneFlags() {{
  const samples = payload.attackAngle?.samples || [];
  const raw = samples.map(rawAttackZoneFlag);
  const filtered = raw.map(() => false);
  let bestStart = -1;
  let bestEnd = -1;
  let bestDistance = Infinity;
  let i = 0;
  while (i < raw.length) {{
    if (!raw[i]) {{ i += 1; continue; }}
    const start = i;
    while (i + 1 < raw.length && raw[i + 1]) i += 1;
    const end = i;
    let segmentDistance = Infinity;
    for (let j = start; j <= end; j++) {{
      const rel = Number(payload.frames[j]?.relativeMs);
      if (Number.isFinite(rel)) segmentDistance = Math.min(segmentDistance, Math.abs(rel));
    }}
    if (segmentDistance < bestDistance) {{
      bestDistance = segmentDistance;
      bestStart = start;
      bestEnd = end;
    }}
    i += 1;
  }}
  if (bestStart >= 0) {{
    for (let j = bestStart; j <= bestEnd; j++) filtered[j] = true;
  }}
  activeAttackZoneFlags = filtered;
}}

function isFrameInDisplayAttackZone(idx) {{
  return Boolean(activeAttackZoneFlags[idx]);
}}

function contactFrameIndex() {{
  let best = 0;
  let bestAbs = Infinity;
  payload.frames.forEach((frame, idx) => {{
    const rel = Math.abs(Number(frame?.relativeMs));
    if (Number.isFinite(rel) && rel < bestAbs) {{
      bestAbs = rel;
      best = idx;
    }}
  }});
  return best;
}}

function intervalZoneFraction(a0, a1, minDeg, maxDeg) {{
  if (!Number.isFinite(a0) || !Number.isFinite(a1)) return 0;
  if (a0 === a1) return (a0 >= minDeg && a0 <= maxDeg) ? 1 : 0;
  const cuts = [0, 1];
  const tMin = (minDeg - a0) / (a1 - a0);
  const tMax = (maxDeg - a0) / (a1 - a0);
  if (tMin > 0 && tMin < 1) cuts.push(tMin);
  if (tMax > 0 && tMax < 1) cuts.push(tMax);
  cuts.sort((a, b) => a - b);
  let frac = 0;
  for (let i = 0; i < cuts.length - 1; i++) {{
    const lo = cuts[i];
    const hi = cuts[i + 1];
    const mid = (lo + hi) / 2;
    const val = a0 + (a1 - a0) * mid;
    if (val >= minDeg && val <= maxDeg) frac += hi - lo;
  }}
  return Math.max(0, Math.min(1, frac));
}}

function intervalZoneValueRange(a0, a1, v0, v1, minDeg, maxDeg) {{
  if (!Number.isFinite(a0) || !Number.isFinite(a1) || !Number.isFinite(v0) || !Number.isFinite(v1)) return [];
  const cuts = [0, 1];
  if (a0 !== a1) {{
    const tMin = (minDeg - a0) / (a1 - a0);
    const tMax = (maxDeg - a0) / (a1 - a0);
    if (tMin > 0 && tMin < 1) cuts.push(tMin);
    if (tMax > 0 && tMax < 1) cuts.push(tMax);
  }}
  cuts.sort((a, b) => a - b);
  const values = [];
  for (let i = 0; i < cuts.length - 1; i++) {{
    const lo = cuts[i];
    const hi = cuts[i + 1];
    const mid = (lo + hi) / 2;
    const val = a0 + (a1 - a0) * mid;
    if (val >= minDeg && val <= maxDeg) {{
      values.push(v0 + (v1 - v0) * lo);
      values.push(v0 + (v1 - v0) * hi);
    }}
  }}
  return values;
}}

function intervalZoneCutPairs(a0, a1, minDeg, maxDeg) {{
  if (!Number.isFinite(a0) || !Number.isFinite(a1)) return [];
  const cuts = [0, 1];
  if (a0 !== a1) {{
    const tMin = (minDeg - a0) / (a1 - a0);
    const tMax = (maxDeg - a0) / (a1 - a0);
    if (tMin > 0 && tMin < 1) cuts.push(tMin);
    if (tMax > 0 && tMax < 1) cuts.push(tMax);
  }}
  cuts.sort((a, b) => a - b);
  const pairs = [];
  for (let i = 0; i < cuts.length - 1; i++) {{
    const lo = cuts[i];
    const hi = cuts[i + 1];
    const mid = (lo + hi) / 2;
    const val = a0 + (a1 - a0) * mid;
    if (val >= minDeg && val <= maxDeg) pairs.push([lo, hi]);
  }}
  return pairs;
}}

function projectedInterpolatedPoint(frameIdx, frac, pointKey, axes, width, height) {{
  const p0 = payload.frames[frameIdx]?.points?.[pointKey]?.xyz;
  const p1 = payload.frames[frameIdx + 1]?.points?.[pointKey]?.xyz;
  if (!p0 || !p1 || p0.some(v => v === null) || p1.some(v => v === null)) return null;
  const p = p0.map((v, idx) => Number(v) + (Number(p1[idx]) - Number(v)) * frac);
  if (p.some(v => !Number.isFinite(v))) return null;
  const [x, y] = scalePoint(p, axes, width, height);
  return {{x, y}};
}}

function ribbonCenterAt(frameIdx, frac, axes, width, height) {{
  const barrel = projectedInterpolatedPoint(frameIdx, frac, "barrel", axes, width, height);
  if (!barrel) return null;
  const handle = projectedInterpolatedPoint(frameIdx, frac, "handle_proxy", axes, width, height);
  let ox = 0;
  let oy = -8;
  if (handle) {{
    const bx = barrel.x - handle.x;
    const by = barrel.y - handle.y;
    const bmag = Math.hypot(bx, by);
    if (bmag > 0.001) {{
      ox = -bx / bmag * 9;
      oy = -by / bmag * 9;
    }}
  }}
  return {{x: barrel.x + ox, y: barrel.y + oy}};
}}
function estimateIdealZoneMetrics() {{
  const samples = payload.attackAngle?.samples || [];
  const segments = [];
  let current = null;
  let windowMs = 0;
  for (let i = 0; i < samples.length - 1; i++) {{
    const s0 = samples[i];
    const s1 = samples[i + 1];
    const t0 = Number(payload.frames[i]?.time);
    const t1 = Number(payload.frames[i + 1]?.time);
    if (!Number.isFinite(t0) || !Number.isFinite(t1) || t1 <= t0) continue;
    const dtMs = (t1 - t0) * 1000;
    const eligible = Boolean(
      s0?.inSwingWindow && s1?.inSwingWindow &&
      s0?.passesSpeedGate && s1?.passesSpeedGate &&
      s0?.passesDirectionGate && s1?.passesDirectionGate
    );
    if (s0?.inSwingWindow && s1?.inSwingWindow) windowMs += dtMs;
    const a0 = Number(s0.attackAngleDeg);
    const a1 = Number(s1.attackAngleDeg);
    const frac = eligible ? intervalZoneFraction(a0, a1, activeIdealMin, activeIdealMax) : 0;
    const ms = frac * dtMs;
    if (ms > 0) {{
      const midRel = ((Number(payload.frames[i]?.relativeMs) || 0) + (Number(payload.frames[i + 1]?.relativeMs) || 0)) / 2;
      if (!current) current = {{ms: 0, nearestContactMs: Infinity, xValues: []}};
      current.ms += ms;
      const xVals = intervalZoneValueRange(a0, a1, Number(s0.barrelXRelativeComIn), Number(s1.barrelXRelativeComIn), activeIdealMin, activeIdealMax);
      current.xValues.push(...xVals);
      if (Number.isFinite(midRel)) current.nearestContactMs = Math.min(current.nearestContactMs, Math.abs(midRel));
    }} else if (current) {{
      segments.push(current);
      current = null;
    }}
  }}
  if (current) segments.push(current);
  let best = segments.sort((a, b) => a.nearestContactMs - b.nearestContactMs)[0];
  if (!best) return {{zoneMs: 0, windowMs, xMin: NaN, xMax: NaN, xRange: NaN}};
  const xVals = best.xValues.filter(v => Number.isFinite(v));
  const xMin = xVals.length ? Math.min(...xVals) : NaN;
  const xMax = xVals.length ? Math.max(...xVals) : NaN;
  return {{zoneMs: best.ms, windowMs, xMin, xMax, xRange: Number.isFinite(xMin) && Number.isFinite(xMax) ? xMax - xMin : NaN}};
}}

function updateZoneSummary() {{
  const el = document.getElementById("zoneSummary");
  if (!el) return;
  const estimate = estimateIdealZoneMetrics();
  const totalMs = estimate.zoneMs;
  const pct = estimate.windowMs > 0 ? totalMs / estimate.windowMs * 100 : NaN;
  const contactOptimal = isFrameInDisplayAttackZone(contactFrameIndex()) ? "Yes" : "No";
  const xRangeText = Number.isFinite(estimate.xMin) && Number.isFinite(estimate.xMax)
    ? `<div>Ideal zone COM-to-barrel out-front range: ${{fmt(estimate.xMin, 1)}} to ${{fmt(estimate.xMax, 1)}} in toward pitcher (${{fmt(estimate.xRange, 1)}} in span).</div>`
    : `<div>Ideal zone COM-to-barrel out-front range: n/a</div>`;
  el.innerHTML = `<div>Ideal zone time: ${{fmt(totalMs, 1)}} ms (${{fmt(pct, 1)}}% of swing window).</div>${{xRangeText}}<div>Optimal range occurred during contact: ${{contactOptimal}}</div>`;
}}

function drawAttackAngleZoneRibbon(ctx, axes, width, height) {{
  if (!traceState.barrel || !payload.attackAngle?.samples) return;
  const samples = payload.attackAngle.samples || [];
  const segments = [];
  let current = null;
  for (let i = 0; i < Math.min(samples.length, payload.frames.length) - 1; i++) {{
    const s0 = samples[i];
    const s1 = samples[i + 1];
    const eligible = Boolean(
      s0?.inSwingWindow && s1?.inSwingWindow &&
      s0?.passesSpeedGate && s1?.passesSpeedGate &&
      s0?.passesDirectionGate && s1?.passesDirectionGate
    );
    const a0 = Number(s0?.attackAngleDeg);
    const a1 = Number(s1?.attackAngleDeg);
    const pairs = eligible ? intervalZoneCutPairs(a0, a1, activeIdealMin, activeIdealMax) : [];
    if (pairs.length) {{
      if (!current) current = {{nearestContactMs: Infinity, intervals: []}};
      const rel0 = Number(payload.frames[i]?.relativeMs);
      const rel1 = Number(payload.frames[i + 1]?.relativeMs);
      pairs.forEach(pair => {{
        const [lo, hi] = pair;
        const midFrac = (lo + hi) / 2;
        const midRel = Number.isFinite(rel0) && Number.isFinite(rel1) ? rel0 + (rel1 - rel0) * midFrac : NaN;
        if (Number.isFinite(midRel)) current.nearestContactMs = Math.min(current.nearestContactMs, Math.abs(midRel));
        current.intervals.push({{frameIdx: i, lo, hi}});
      }});
    }} else if (current) {{
      segments.push(current);
      current = null;
    }}
  }}
  if (current) segments.push(current);
  const best = segments.sort((a, b) => a.nearestContactMs - b.nearestContactMs)[0];
  if (!best) return;
  const centers = [];
  best.intervals.forEach(interval => {{
    if (interval.frameIdx >= frameIndex) return;
    const start = ribbonCenterAt(interval.frameIdx, interval.lo, axes, width, height);
    const stop = ribbonCenterAt(interval.frameIdx, interval.hi, axes, width, height);
    if (!start || !stop) return;
    if (!centers.length || Math.hypot(centers[centers.length - 1].x - start.x, centers[centers.length - 1].y - start.y) > 0.25) centers.push(start);
    centers.push(stop);
  }});
  if (centers.length) drawRibbonSegment(ctx, centers);
}}
function drawRibbonSegment(ctx, centers) {{
  if (centers.length < 2) return;
  const upper = [];
  const lower = [];
  const halfWidth = 7;
  for (let i = 0; i < centers.length; i++) {{
    const prev = centers[Math.max(0, i - 1)];
    const next = centers[Math.min(centers.length - 1, i + 1)];
    let tx = next.x - prev.x;
    let ty = next.y - prev.y;
    const mag = Math.hypot(tx, ty);
    if (!Number.isFinite(mag) || mag < 0.001) continue;
    tx /= mag;
    ty /= mag;
    const nx = -ty;
    const ny = tx;
    upper.push({{x: centers[i].x + nx * halfWidth, y: centers[i].y + ny * halfWidth}});
    lower.push({{x: centers[i].x - nx * halfWidth, y: centers[i].y - ny * halfWidth}});
  }}
  if (upper.length < 2 || lower.length < 2) return;
  ctx.save();
  ctx.fillStyle = "rgba(239, 68, 68, 0.24)";
  ctx.strokeStyle = "rgba(239, 68, 68, 0.55)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(upper[0].x, upper[0].y);
  upper.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
  lower.slice().reverse().forEach(p => ctx.lineTo(p.x, p.y));
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}}
function drawInflectionMarker(ctx, marker, axes, width, height) {{
  if (!traceState[marker.pointKey]) return;
  const frame = payload.frames[marker.frame];
  const p = frame?.points?.[marker.pointKey]?.xyz;
  if (!p || p.some(v => v === null)) return;
  const [x, y] = scalePoint(p, axes, width, height);
  ctx.save();
  ctx.fillStyle = "#111111";
  ctx.beginPath();
  const traceWidth = marker.pointKey === "barrel" ? 3 : 2;
  ctx.arc(x, y, traceWidth / 2, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}}

function drawAccelerationVector(ctx, tracer, axes, axesKey, width, height) {{
  if (!traceState[tracer.pointKey]) return;
  const velocity = payload.velocities[tracer.pointKey];
  if (!velocity) return;
  const sample = velocity.samples[frameIndex];
  const frame = payload.frames[frameIndex];
  const p = frame?.points?.[tracer.pointKey]?.xyz;
  if (!sample || !p || p.some(v => v === null)) return;
  if (!Number.isFinite(sample.speed) || sample.speed <= 0) return;

  const fullVector = [sample.ax3, sample.ay3, sample.az3];
  const hasFullVector = fullVector.every(v => Number.isFinite(v));
  if (!hasFullVector && velocity.axesKey !== axesKey) return;

  const p2 = [...p];
  if (hasFullVector) {{
    p2[0] += fullVector[0] * 0.001;
    p2[1] += fullVector[1] * 0.001;
    p2[2] += fullVector[2] * 0.001;
  }} else {{
    p2[axes[0].idx] += sample.vx * 0.001;
    p2[axes[1].idx] += sample.vy * 0.001;
  }}
  const [x1, y1] = scalePoint(p, axes, width, height);
  const [x2, y2] = scalePoint(p2, axes, width, height);
  const dx = x2 - x1;
  const dy = y2 - y1;
  const mag = Math.hypot(dx, dy);
  if (!Number.isFinite(mag) || mag < 0.001) return;
  const pct = Math.max(0, Math.min(1, sample.pctMax || 0));
  const length = 10 + pct * 34;
  const ux = dx / mag;
  const uy = dy / mag;
  const endX = x1 + ux * length;
  const endY = y1 + uy * length;
  const head = 6;
  const angle = Math.atan2(uy, ux);
  ctx.save();
  ctx.strokeStyle = tracer.color;
  ctx.fillStyle = tracer.color;
  ctx.lineWidth = 2;
  ctx.globalAlpha = 0.95;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(endX, endY);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(endX, endY);
  ctx.lineTo(endX - head * Math.cos(angle - Math.PI / 6), endY - head * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(endX - head * Math.cos(angle + Math.PI / 6), endY - head * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}}

function drawView(canvas, axes, axesKey) {{
  const [ctx, width, height] = resizeCanvas(canvas);
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#e5eaf0";
  ctx.lineWidth = 1;
  ctx.strokeRect(28, 18, width - 56, height - 52);

  const current = payload.frames[frameIndex];
  payload.stickSegments.forEach(segment => drawSegment(ctx, current.points, segment, axes, width, height));
  payload.tracers.forEach(tracer => drawTrace(ctx, tracer, axes, width, height));
  drawAttackAngleZoneRibbon(ctx, axes, width, height);
  payload.inflectionMarkers.forEach(marker => drawInflectionMarker(ctx, marker, axes, width, height));
  if (!payload.viewerOptions?.hideAccelerationVectors) {{
    payload.tracers.forEach(tracer => drawAccelerationVector(ctx, tracer, axes, axesKey, width, height));
  }}

  Object.values(current.points).forEach(point => {{
    if (point.draw === false) return;
    if (payload.viewerOptions?.hidePointKeys?.includes(point.key)) return;
    if (!point.xyz || point.xyz.some(v => v === null)) return;
    const [x, y] = scalePoint(point.xyz, axes, width, height);
    let color = point.color;
    if (payload.viewerOptions?.singleLandmarkColor && point.key !== "barrel" && point.key !== "center_mass") {{
      color = payload.viewerOptions.singleLandmarkColor;
    }}
    ctx.fillStyle = color;
    ctx.beginPath();
    const radius = point.key === "barrel" ? 4 : 4;
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }});

  drawTimeline(ctx, width, height);
}}

function drawTimeline(ctx, width, height) {{
  const y = height - 14;
  ctx.strokeStyle = "#cbd5e1";
  ctx.beginPath();
  ctx.moveTo(28, y);
  ctx.lineTo(width - 28, y);
  ctx.stroke();
  (payload.searchWindows || []).forEach(window => {{
    const startX = 28 + window.startFrame / Math.max(1, payload.frames.length - 1) * (width - 56);
    const endX = 28 + window.endFrame / Math.max(1, payload.frames.length - 1) * (width - 56);
    ctx.save();
    ctx.strokeStyle = window.color || "#0984e3";
    ctx.globalAlpha = 0.35;
    ctx.lineWidth = 8;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(startX, y);
    ctx.lineTo(endX, y);
    ctx.stroke();
    ctx.restore();
  }});
  payload.events.forEach(event => {{
    const x = 28 + event.frame / Math.max(1, payload.frames.length - 1) * (width - 56);
    ctx.strokeStyle = event.color;
    ctx.lineWidth = event.name === "contact" ? 3 : 2;
    ctx.beginPath();
    ctx.moveTo(x, y - 12);
    ctx.lineTo(x, y + 2);
    ctx.stroke();
  }});
  const cx = 28 + frameIndex / Math.max(1, payload.frames.length - 1) * (width - 56);
  ctx.strokeStyle = "#111111";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx, 18);
  ctx.lineTo(cx, y + 4);
  ctx.stroke();
}}

function fmt(value, digits = 1) {{
  return Number.isFinite(value) ? value.toFixed(digits) : "";
}}

function updateTables() {{
  const eventRows = [];
  let lastGroup = null;
  const events = [...payload.events].sort((a, b) => {{
    const ga = Number.isFinite(a.groupOrder) ? a.groupOrder : 99;
    const gb = Number.isFinite(b.groupOrder) ? b.groupOrder : 99;
    const oa = Number.isFinite(a.order) ? a.order : 99;
    const ob = Number.isFinite(b.order) ? b.order : 99;
    if (ga !== gb) return ga - gb;
    if (oa !== ob) return oa - ob;
    return a.relativeMs - b.relativeMs;
  }});
  events.forEach(event => {{
    const group = event.group || "Other";
    if (group !== lastGroup) {{
      eventRows.push(`<tr class="event-group"><td colspan="3">${{group}}</td></tr>`);
      lastGroup = group;
    }}
    eventRows.push(`
      <tr>
        <td><span class="swatch" style="background:${{event.color}}"></span>${{event.name}}</td>
        <td>${{fmt(event.relativeMs)}} ms</td>
        <td><button onclick="go(${{event.frame}})">Go</button></td>
      </tr>
    `);
  }});
  document.getElementById("events").innerHTML = eventRows.join("");

  const metricsEl = document.getElementById("metrics");
  if (metricsEl) {{
    metricsEl.innerHTML = Object.entries(payload.metrics).map(([key, value]) => `
      <tr><td>${{key}}</td><td>${{fmt(value, 2)}}</td></tr>
    `).join("");
  }}

  document.getElementById("metadata").innerHTML = Object.entries(payload.metadata).filter(([key]) => key !== "bat_speed_mph_max_x").map(([key, value]) => `
    <tr><td>${{key}}</td><td>${{value}}</td></tr>
  `).join("");

  const contactMetricsEl = document.getElementById("contactMetrics");
  if (contactMetricsEl) {{
    const rows = Object.entries(payload.contactMetrics || {{}}).map(([key, item]) => `
      <tr><td>${{item.label || key}}</td><td>${{fmt(item.value, 1)}}${{item.units ? " " + item.units : ""}}</td></tr>
    `);
    contactMetricsEl.innerHTML = rows.length ? rows.join("") : `<tr><td colspan="2">No contact metrics</td></tr>`;
  }}

  const legendEl = document.getElementById("legend");
  if (payload.viewerOptions?.hidePointLegend) {{
    legendEl.innerHTML = "";
    legendEl.style.display = "none";
  }} else {{
    const pointMap = payload.frames[0].points;
    legendEl.innerHTML = Object.values(pointMap).filter(point => point.draw !== false).map(point => `
      <span><span class="swatch" style="background:${{point.color}}"></span>${{point.label}}</span>
    `).join("");
  }}

  const windowEl = document.getElementById("searchWindows");
  const windows = payload.searchWindows || [];
  if (windowEl && windows.length) {{
    windowEl.innerHTML = "<strong>Search Windows</strong>" + windows.map(window => `
      <span title="${{window.description}}">
        <span class="swatch" style="background:${{window.color}}"></span>
        ${{window.label}}: ${{fmt(window.startRelativeMs)}} to ${{fmt(window.endRelativeMs)}} ms
        <span class="velocity-readout">${{window.source}}; nearest frames ${{fmt(window.startFrameRelativeMs)}} to ${{fmt(window.endFrameRelativeMs)}} ms</span>
      </span>
    `).join("");
  }} else if (windowEl) {{
    windowEl.innerHTML = "";
  }}
}}

function updateTraceControls() {{
  const controls = document.getElementById("traceControls");
  controls.innerHTML = "<strong>Traces</strong>" + payload.tracers.map(tracer => `
    <label title="${{tracer.label}} trace">
      <input type="checkbox" data-trace="${{tracer.pointKey}}" ${{traceState[tracer.pointKey] ? "checked" : ""}}>
      <span class="swatch" style="background:${{tracer.color}}"></span>${{tracer.label}}
      <span class="velocity-readout" id="velo-${{tracer.pointKey}}"></span>
    </label>
  `).join("");
  controls.querySelectorAll("input[data-trace]").forEach(input => {{
    input.onchange = () => {{
      traceState[input.dataset.trace] = input.checked;
      render();
    }};
  }});
}}

function updateVelocityReadouts() {{
  payload.tracers.forEach(tracer => {{
    const el = document.getElementById(`velo-${{tracer.pointKey}}`);
    if (!el) return;
    if (!traceState[tracer.pointKey]) {{
      el.textContent = "";
      return;
    }}
    let text = "";
    if (tracer.pointKey === "barrel" && payload.attackAngle?.samples?.[frameIndex]) {{
      const aa = payload.attackAngle.samples[frameIndex];
      const speedPct = Number.isFinite(aa.sweetSpotSpeedPctMax) ? aa.sweetSpotSpeedPctMax * 100 : NaN;
      const speedGatePct = Number.isFinite(payload.attackAngle.speedGatePct) ? payload.attackAngle.speedGatePct * 100 : NaN;
      const batSpeedMph = Number.isFinite(aa.sweetSpotSpeedMps) ? aa.sweetSpotSpeedMps * 2.2369362920544 : NaN;
      const ad = Number.isFinite(aa.attackDirectionDeg) ? aa.attackDirectionDeg : NaN;
      const adLabel = Number.isFinite(ad) ? (ad > 2 ? "pull" : (ad < -2 ? "oppo" : "middle")) : "";
      const adText = Number.isFinite(ad) ? `, AD ${{fmt(ad, 1)}} deg ${{adLabel}}` : "";
      const speedGateText = Number.isFinite(speedGatePct) ? `, Bat Speed ${{fmt(batSpeedMph, 1)}} mph (${{fmt(speedPct, 0)}}% / gate ${{fmt(speedGatePct, 0)}}%)` : "";
      text = `AA ${{fmt(aa.attackAngleDeg, 1)}} deg${{adText}}${{speedGateText}}`;
    }} else if (payload.velocities?.[tracer.pointKey]?.samples?.[frameIndex]) {{
      const velo = payload.velocities[tracer.pointKey];
      const sample = velo.samples[frameIndex];
      const val = Number.isFinite(sample.displaySpeed) ? Math.abs(sample.displaySpeed) : NaN;
      const pct = Number.isFinite(sample.displayPctMax) ? sample.displayPctMax * 100 : NaN;
      if (Number.isFinite(val)) {{
        text = `${{velo.displayLabel || "Velocity"}} ${{fmt(val, velo.displayUnits === "deg/s" ? 0 : 2)}} ${{velo.displayUnits || ""}} (${{fmt(pct, 0)}}% max)`;
      }}
    }}
    el.textContent = text;
  }});
}}

function render() {{
  frameIndex = Math.max(0, Math.min(payload.frames.length - 1, frameIndex));
  slider.value = frameIndex;
  const f = payload.frames[frameIndex];
  document.getElementById("frameLabel").textContent = `Frame ${{frameIndex + 1}} / ${{payload.frames.length}}`;
  document.getElementById("timeText").textContent = `${{fmt(f.relativeMs)}} ms from contact`;
  updateVelocityReadouts();
  updateZoneSummary();
  drawView(side, AXES.side, "side");
  drawView(topCanvas, AXES.top, "top");
  drawView(front, AXES.front, "front");
}}

function go(idx) {{
  frameIndex = idx;
  playing = false;
  play.textContent = "Play";
  render();
}}

document.getElementById("back").onclick = () => {{ frameIndex -= 1; render(); }};
document.getElementById("forward").onclick = () => {{ frameIndex += 1; render(); }};
slider.oninput = () => {{ frameIndex = Number(slider.value); render(); }};
const idealMinInput = document.getElementById("idealMin");
const idealMaxInput = document.getElementById("idealMax");
if (idealMinInput && idealMaxInput) {{
  activeIdealMin = Math.round(activeIdealMin);
  activeIdealMax = Math.round(activeIdealMax);
  idealMinInput.value = activeIdealMin;
  idealMaxInput.value = activeIdealMax;
  const updateIdealRange = () => {{
    const minVal = Math.round(Number(idealMinInput.value));
    const maxVal = Math.round(Number(idealMaxInput.value));
    if (Number.isFinite(minVal) && Number.isFinite(maxVal) && minVal < maxVal) {{
      activeIdealMin = minVal;
      activeIdealMax = maxVal;
      idealMinInput.value = activeIdealMin;
      idealMaxInput.value = activeIdealMax;
      recalculateAttackZoneFlags();
      render();
    }}
  }};
  idealMinInput.onchange = updateIdealRange;
  idealMaxInput.onchange = updateIdealRange;
}}
play.onclick = () => {{
  playing = !playing;
  play.textContent = playing ? "Pause" : "Play";
  if (playing) {{
    timer = setInterval(() => {{
      frameIndex = (frameIndex + 1) % payload.frames.length;
      render();
    }}, 60);
  }} else {{
    clearInterval(timer);
  }}
}};
window.addEventListener("resize", render);
updateTables();
updateTraceControls();
recalculateAttackZoneFlags();
render();
</script>
</body>
</html>
"""


def add_virtual_trace_points(points: dict, hitter_side: str) -> None:
    pelvis = midpoint(points.get("left_hip"), points.get("right_hip"))
    if pelvis is not None:
        points["pelvis"] = {
            "label": "pelvis",
            "key": "pelvis",
            "color": EVENT_COLORS["pelvis_onset_time"],
            "draw": False,
            "xyz": pelvis,
        }

    torso = midpoint(points.get("left_shoulder"), points.get("right_shoulder"))
    if torso is None and "thorax" in points:
        torso = points["thorax"]["xyz"]
    if torso is not None:
        points["torso"] = {
            "label": "torso",
            "key": "torso",
            "color": EVENT_COLORS["torso_onset_time"],
            "draw": False,
            "xyz": torso,
        }

    lead_side = {"R": "left", "L": "right"}.get(hitter_side)
    if lead_side:
        elbow_key = f"{lead_side}_elbow"
        hand_key = f"{lead_side}_hand"
        if elbow_key in points:
            points["lead_arm"] = {
                "label": "lead arm",
                "color": EVENT_COLORS["lead_arm_onset_time"],
                "draw": False,
                "xyz": points[elbow_key]["xyz"],
            }
        if hand_key in points:
            points["lead_hand"] = {
                "label": "lead hand",
                "color": EVENT_COLORS["lead_hand_onset_time"],
                "draw": False,
                "xyz": points[hand_key]["xyz"],
            }

    back_side = {"R": "right", "L": "left"}.get(hitter_side)
    if back_side:
        elbow_key = f"{back_side}_elbow"
        if elbow_key in points:
            points["back_elbow"] = {
                "label": "back elbow",
                "color": "#a855f7",
                "draw": False,
                "xyz": points[elbow_key]["xyz"],
            }


def midpoint(a: dict | None, b: dict | None) -> list[float | None] | None:
    if not a or not b:
        return None
    av = a.get("xyz")
    bv = b.get("xyz")
    if not av or not bv or any(v is None for v in av) or any(v is None for v in bv):
        return None
    return [(av[i] + bv[i]) / 2.0 for i in range(3)]


def build_tracers(onsets: pd.Series, frames: list[dict]) -> list[dict]:
    tracers = []
    for label, point_key, onset_col, color in TRACE_DEFS:
        onset = (
            pd.to_numeric(pd.Series([onsets.get(onset_col)]), errors="coerce").iloc[0]
            if onset_col
            else np.nan
        )
        axes_key, _, axis_label = TRACE_AXES[point_key]
        tracers.append(
            {
                "label": label,
                "pointKey": point_key,
                "onsetColumn": onset_col,
                "axesKey": axes_key,
                "axisLabel": axis_label,
                "gatePct": TRACE_GATE_PCT[point_key],
                "onsetFrame": nearest_frame(frames, float(onset)) if np.isfinite(onset) else None,
                "startFrame": 0,
                "relativeMs": clean_float((float(onset) - first_contact_time(frames)) * 1000.0)
                if np.isfinite(onset)
                else None,
                "color": color,
                "defaultOn": point_key == "barrel",
            }
        )
    return tracers


def build_inflection_markers(onsets: pd.Series, frames: list[dict]) -> list[dict]:
    markers = []
    contact_time = first_contact_time(frames)
    for label, point_key, onset_col, color in TRACE_DEFS:
        if not onset_col:
            continue
        inflection_col = onset_col.replace("_onset_time", "_inflection_time")
        inflection = pd.to_numeric(pd.Series([onsets.get(inflection_col)]), errors="coerce").iloc[0]
        if not np.isfinite(inflection):
            continue
        marker_point_key = point_key
        marker_label = label
        method_col = onset_col.replace("_onset_time", "_onset_method")
        method = str(onsets.get(method_col, ""))
        if point_key == "lead_hand" and "barrel_x_reversal" in method:
            marker_point_key = "barrel"
            marker_label = "lead hand/barrel reversal"
        markers.append(
            {
                "label": marker_label,
                "pointKey": marker_point_key,
                "inflectionColumn": inflection_col,
                "frame": nearest_frame(frames, float(inflection)),
                "time": clean_float(float(inflection)),
                "relativeMs": clean_float((float(inflection) - contact_time) * 1000.0),
                "color": color,
            }
        )
    return markers


def build_velocity_series(
    frames: list[dict],
    contact_time: float,
    joint_velos: pd.DataFrame,
    trace_percent_windows: dict[str, tuple[float, float]] | None = None,
) -> dict[str, dict]:
    trace_percent_windows = trace_percent_windows or {}
    velocities = {}
    time = np.asarray([frame["time"] for frame in frames], dtype=float)
    if len(time) < 4:
        return velocities
    dt = median_dt(time)
    if not np.isfinite(dt) or dt <= 0:
        return velocities

    angular = build_angular_display_series(frames, time, contact_time, joint_velos, trace_percent_windows)

    for label, point_key, _, _ in TRACE_DEFS:
        axes_key, axes, axis_label = TRACE_AXES[point_key]
        xyz = np.asarray(
            [
                frame["points"].get(point_key, {}).get("xyz", [np.nan, np.nan, np.nan])
                for frame in frames
            ],
            dtype=float,
        )
        valid = np.isfinite(time) & np.isfinite(xyz).all(axis=1)
        if valid.sum() < 4:
            continue

        smoothed_xyz = xyz.copy()
        smoothed_xyz[valid] = smooth_positions(smoothed_xyz[valid], dt, PRIMARY_CONFIG.smooth_ms)
        vel_xyz = np.full_like(smoothed_xyz, np.nan)
        accel_xyz = np.full_like(smoothed_xyz, np.nan)
        for axis_i in range(3):
            vel_xyz[valid, axis_i] = np.gradient(smoothed_xyz[valid, axis_i], time[valid])
            accel_xyz[valid, axis_i] = np.gradient(vel_xyz[valid, axis_i], time[valid])

        vx_proj = vel_xyz[:, axes[0]]
        vy_proj = vel_xyz[:, axes[1]]
        projected_speed = np.sqrt(vx_proj * vx_proj + vy_proj * vy_proj)
        eligible = trace_percent_window_mask(time, valid, contact_time, point_key, trace_percent_windows)
        if not eligible.any():
            eligible = valid & (time <= contact_time)
        max_projected_speed = float(np.nanmax(projected_speed[eligible])) if eligible.any() else np.nan
        samples = []
        for i in range(len(frames)):
            current_speed = projected_speed[i]
            pct_max = current_speed / max_projected_speed if np.isfinite(current_speed) and max_projected_speed > 0 else np.nan
            samples.append(
                {
                    "vx": clean_float(vx_proj[i]),
                    "vy": clean_float(vy_proj[i]),
                    "ax3": clean_float(accel_xyz[i, 0]),
                    "ay3": clean_float(accel_xyz[i, 1]),
                    "az3": clean_float(accel_xyz[i, 2]),
                    "speed": clean_float(current_speed),
                    "pctMax": clean_float(pct_max),                }
        )

        display = angular.get(point_key)
        if display is None:
            display_speed = projected_speed
            max_display_speed = max_projected_speed
            display_pct = (
                projected_speed / max_projected_speed if np.isfinite(max_projected_speed) and max_projected_speed > 0 else np.full(len(frames), np.nan)
            )
            display_units = "m/s"
            display_label = f"projected velocity {axis_label}"
        else:
            display_speed = display["speed"]
            max_display_speed = display["max_speed"]
            display_pct = (
                np.abs(display_speed) / max_display_speed
                if np.isfinite(max_display_speed) and max_display_speed > 0
                else np.full(len(frames), np.nan)
            )
            display_units = "deg/s"
            display_label = display["label"]

        velocities[point_key] = {
            "label": label,
            "axesKey": axes_key,
            "axisLabel": axis_label,
            "gatePct": TRACE_GATE_PCT[point_key],
            "maxPrecontactSpeed": clean_float(max_projected_speed),
            "maxDisplaySpeed": clean_float(max_display_speed),
            "displayUnits": display_units,
            "displayLabel": display_label,
            "samples": samples,
        }
        for i, sample in enumerate(velocities[point_key]["samples"]):
            sample["displaySpeed"] = clean_float(display_speed[i])
            sample["displayPctMax"] = clean_float(display_pct[i])
    return velocities


def build_angular_display_series(
    frames: list[dict],
    frame_time: np.ndarray,
    contact_time: float,
    joint_velos: pd.DataFrame,
    trace_percent_windows: dict[str, tuple[float, float]] | None = None,
) -> dict[str, dict[str, object]]:
    trace_percent_windows = trace_percent_windows or {}
    angular: dict[str, dict[str, object]] = {}
    if not joint_velos.empty:
        g = joint_velos.sort_values("time").copy()
        for col in g.columns:
            if col != "session_swing":
                g[col] = pd.to_numeric(g[col], errors="coerce")
        jt = g["time"].to_numpy(float) if "time" in g else np.array([])
        for point_key, cols in ANGULAR_VELOCITY_COLS.items():
            if len(jt) < 2 or not set(cols).issubset(g.columns):
                continue
            arr = g[cols].to_numpy(float)
            mag = np.linalg.norm(arr, axis=1)
            valid = np.isfinite(jt) & np.isfinite(mag)
            if valid.sum() < 2:
                continue
            dt = median_dt(jt[valid])
            if not np.isfinite(dt) or dt <= 0:
                continue
            mag[valid] = smooth_positions(mag[valid, None], dt, PRIMARY_CONFIG.smooth_ms).ravel()
            velocity = np.interp(frame_time, jt[valid], mag[valid], left=np.nan, right=np.nan)
            max_velocity = max_precontact_value(
                frame_time,
                velocity,
                contact_time,
                point_key=point_key,
                trace_percent_windows=trace_percent_windows,
            )
            angular[point_key] = {
                "speed": velocity,
                "max_speed": max_velocity,
                "label": "angular velocity",
            }

    barrel_speed = build_barrel_angular_speed(frames, frame_time, contact_time, trace_percent_windows)
    if barrel_speed is not None:
        angular["barrel"] = barrel_speed
    return angular


def build_barrel_angular_speed(
    frames: list[dict],
    frame_time: np.ndarray,
    contact_time: float,
    trace_percent_windows: dict[str, tuple[float, float]] | None = None,
) -> dict[str, object] | None:
    handle = np.asarray(
        [
            frame["points"].get("handle_proxy", {}).get("xyz", [np.nan, np.nan, np.nan])
            for frame in frames
        ],
        dtype=float,
    )
    barrel = np.asarray(
        [
            frame["points"].get("barrel", {}).get("xyz", [np.nan, np.nan, np.nan])
            for frame in frames
        ],
        dtype=float,
    )
    valid = np.isfinite(frame_time) & np.isfinite(handle).all(axis=1) & np.isfinite(barrel).all(axis=1)
    if valid.sum() < 4:
        return None
    dt = median_dt(frame_time[valid])
    if not np.isfinite(dt) or dt <= 0:
        return None

    bat_vector = barrel - handle
    bat_vector[valid] = smooth_positions(bat_vector[valid], dt, PRIMARY_CONFIG.smooth_ms)
    d_vector = np.full_like(bat_vector, np.nan)
    for axis in range(3):
        d_vector[valid, axis] = np.gradient(bat_vector[valid, axis], frame_time[valid])

    cross_mag = np.linalg.norm(np.cross(bat_vector, d_vector), axis=1)
    vector_len_sq = np.sum(bat_vector * bat_vector, axis=1)
    omega_rad_s = cross_mag / np.maximum(vector_len_sq, 1e-9)
    omega_deg_s = omega_rad_s * 180.0 / np.pi
    omega_deg_s[~valid] = np.nan
    omega_smooth = omega_deg_s.copy()
    omega_smooth[valid] = smooth_positions(omega_smooth[valid, None], dt, PRIMARY_CONFIG.smooth_ms).ravel()
    signed_accel = np.full(len(frame_time), np.nan)
    signed_accel[valid] = np.gradient(omega_smooth[valid], frame_time[valid])
    signed_accel[valid] = smooth_positions(signed_accel[valid, None], dt, PRIMARY_CONFIG.smooth_ms).ravel()
    max_accel = max_abs_precontact_value(
        frame_time,
        signed_accel,
        contact_time,
        point_key="barrel",
        trace_percent_windows=trace_percent_windows,
    )
    return {
        "speed": signed_accel,
        "max_speed": max_accel,
        "label": "derived bat angular accel",
    }


def max_precontact_value(
    time: np.ndarray,
    values: np.ndarray,
    contact_time: float,
    point_key: str = "",
    trace_percent_windows: dict[str, tuple[float, float]] | None = None,
) -> float:
    eligible = trace_percent_window_mask(time, np.isfinite(values), contact_time, point_key, trace_percent_windows)
    if not eligible.any():
        eligible = np.isfinite(time) & np.isfinite(values) & (time <= contact_time)
    return float(np.nanmax(values[eligible])) if eligible.any() else np.nan


def max_abs_precontact_value(
    time: np.ndarray,
    values: np.ndarray,
    contact_time: float,
    point_key: str = "",
    trace_percent_windows: dict[str, tuple[float, float]] | None = None,
) -> float:
    eligible = trace_percent_window_mask(time, np.isfinite(values), contact_time, point_key, trace_percent_windows)
    if not eligible.any():
        eligible = np.isfinite(time) & np.isfinite(values) & (time <= contact_time)
    return float(np.nanmax(np.abs(values[eligible]))) if eligible.any() else np.nan


def trace_percent_window_mask(
    time: np.ndarray,
    valid: np.ndarray,
    contact_time: float,
    point_key: str,
    trace_percent_windows: dict[str, tuple[float, float]] | None = None,
) -> np.ndarray:
    if trace_percent_windows and point_key in trace_percent_windows:
        start_time, end_time = trace_percent_windows[point_key]
        return np.isfinite(time) & valid & (time >= start_time) & (time <= end_time)
    start_ms, end_ms = TRACE_PERCENT_WINDOW_OVERRIDES_MS.get(point_key, TRACE_PERCENT_WINDOW_MS)
    rel_ms = (time - contact_time) * 1000.0
    return np.isfinite(time) & valid & (rel_ms >= start_ms) & (rel_ms <= end_ms)


def first_contact_time(frames: list[dict]) -> float:
    zero_frame = min(frames, key=lambda frame: abs(frame["relativeMs"] or 0.0))
    return float(zero_frame["time"])


def has_xyz(df: pd.DataFrame, prefix: str) -> bool:
    return all(f"{prefix}_{axis}" in df.columns for axis in ["x", "y", "z"])


def reverse_lookup(rename: dict[str, str], display_prefix: str) -> str:
    for real, display in rename.items():
        if display == display_prefix:
            return real
    return display_prefix


def calculate_bounds(df: pd.DataFrame, prefixes: list[str]) -> dict:
    values = {"x": [], "y": [], "z": []}
    for prefix in prefixes:
        for axis in values:
            col = f"{prefix}_{axis}"
            if col in df:
                values[axis].extend(pd.to_numeric(df[col], errors="coerce").dropna().tolist())
    bounds = {}
    for axis, vals in values.items():
        arr = np.asarray(vals, dtype=float)
        if len(arr) == 0:
            bounds[axis] = {"min": 0.0, "max": 1.0}
            continue
        lo = float(np.nanmin(arr))
        hi = float(np.nanmax(arr))
        if axis == "z":
            lo = min(lo, 0.0)
        pad = max(0.05, (hi - lo) * 0.12)
        bounds[axis] = {"min": lo - pad, "max": hi + pad}
    return bounds


def extract_points(df: pd.DataFrame, prefix: str) -> list[list[float | None]]:
    if not has_xyz(df, prefix):
        return []
    return [
        [clean_float(row[f"{prefix}_x"]), clean_float(row[f"{prefix}_y"]), clean_float(row[f"{prefix}_z"])]
        for _, row in df.iterrows()
    ]


def nearest_frame(frames: list[dict], time: float) -> int:
    return int(np.argmin([abs(frame["time"] - time) for frame in frames]))


def first_valid(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    return float(vals.iloc[0]) if len(vals) else np.nan


def clean_float(value) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if np.isfinite(out) else None


def clean_value(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (np.integer, np.floating)):
        return clean_float(value)
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())












