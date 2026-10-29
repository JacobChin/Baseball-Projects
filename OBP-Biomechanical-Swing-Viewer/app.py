from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from scripts.create_swing_qc_viewer import render_html


ROOT = Path(__file__).resolve().parent
METRICS_PATH = ROOT / "outputs" / "attack_angle_zone_metrics.csv"
MANIFEST_PATH = ROOT / "outputs" / "swing_manifest.csv"
PAYLOAD_DIR = ROOT / "Viewer-Payloads"
VIEWER_DIRS = (ROOT / "outputs" / "qc_viewers", ROOT / "Viewer-Examples")
IGNORED_VIEWERS = {"index", "definitions"}

FILTER_DEFINITIONS = (
    (
        "Bat speed (mph)",
        "attack_angle_contact_bat_speed_mph",
        "bat_speed",
    ),
    (
        "Attack angle (deg)",
        "attack_angle_contact_computed_deg",
        "attack_angle",
    ),
    (
        "Swing length (in)",
        "swing_length_from_barrel_inflection_in",
        "swing_length",
    ),
    (
        "Ideal zone time (ms)",
        "attack_zone_time_ms",
        "ideal_zone_time",
    ),
)
OPERATORS = ("Any", ">", ">=", "=", "<=", "<")


st.set_page_config(
    page_title="OBP Biomechanical Swing Viewer",
    page_icon=":material/sports_baseball:",
    layout="wide",
)
st.markdown(
    """
    <style>
    .block-container {max-width: 1600px; padding-top: 1.25rem; padding-bottom: 2rem;}
    [data-testid="stSidebar"] {min-width: 330px; max-width: 330px;}
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {gap: 0.45rem;}
    @media (max-width: 768px) {
        h1 {font-size: 2.25rem !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def natural_swing_key(value: str) -> tuple[int, int, str]:
    try:
        session, swing = value.split("_", maxsplit=1)
        return int(session), int(swing), value
    except (TypeError, ValueError):
        return 10**9, 10**9, str(value)


def viewer_id(path: Path) -> str:
    name = path.name
    for suffix in (".json.gz", ".html.gz"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


@st.cache_data(show_spinner=False)
def discover_viewers() -> dict[str, Path]:
    viewers: dict[str, Path] = {}

    for directory in reversed(VIEWER_DIRS):
        if not directory.exists():
            continue
        for pattern in ("*.html", "*.html.gz"):
            for path in sorted(directory.glob(pattern)):
                swing_id = viewer_id(path)
                if swing_id.lower() not in IGNORED_VIEWERS:
                    viewers[swing_id] = path

    if PAYLOAD_DIR.exists():
        for path in sorted(PAYLOAD_DIR.glob("*.json.gz")):
            viewers[viewer_id(path)] = path

    return dict(sorted(viewers.items(), key=lambda item: natural_swing_key(item[0])))


@st.cache_data(show_spinner="Loading swing measurements...")
def load_catalog(viewer_ids: tuple[str, ...]) -> pd.DataFrame:
    metrics = pd.read_csv(METRICS_PATH)
    manifest = pd.read_csv(MANIFEST_PATH)

    metric_columns = [
        column
        for column in (
            "session_swing",
            "user",
            "session",
            "highest_playing_level",
            "hitter_side",
            "attack_angle_contact_bat_speed_mph",
            "attack_angle_contact_computed_deg",
            "attack_zone_time_ms",
            "swing_length_from_barrel_inflection_in",
            "contact_barrel_x_relative_com_in",
            "swing_path_tilt_contact_deg",
            "attack_direction_contact_pull_deg",
            "attack_zone_pct_of_swing",
            "attack_zone_depth_range_in",
            "attack_angle_qc",
            "model_ready_primary",
        )
        if column in metrics.columns
    ]
    manifest_columns = [
        column
        for column in (
            "session_swing",
            "session_height_in",
            "athlete_age",
            "bat_weight_oz",
            "bat_length_in",
            "exit_velo_mph_x",
            "has_hittrax",
            "has_force",
        )
        if column in manifest.columns
    ]

    catalog = metrics[metric_columns].copy()
    manifest_subset = manifest[manifest_columns].copy()
    duplicate_columns = set(catalog.columns) & set(manifest_subset.columns) - {
        "session_swing"
    }
    manifest_subset = manifest_subset.drop(
        columns=list(duplicate_columns),
        errors="ignore",
    )
    catalog = catalog.merge(manifest_subset, on="session_swing", how="left")
    catalog["session_swing"] = catalog["session_swing"].astype(str)
    catalog = catalog[catalog["session_swing"].isin(viewer_ids)].copy()
    catalog["viewer_order"] = catalog["session_swing"].map(
        {swing_id: index for index, swing_id in enumerate(viewer_ids)}
    )
    return catalog.sort_values("viewer_order").reset_index(drop=True)


@st.cache_data(
    show_spinner="Opening interactive swing viewer...",
    max_entries=8,
)
def read_viewer(path_string: str, modified_ns: int) -> str:
    del modified_ns
    path = Path(path_string)
    if path.name.endswith(".json.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return render_html(json.load(handle))
    if path.name.endswith(".html.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8")


def apply_numeric_filter(
    data: pd.DataFrame,
    column: str,
    operator: str,
    target: float,
) -> pd.DataFrame:
    if operator == "Any":
        return data

    values = pd.to_numeric(data[column], errors="coerce")
    if operator == ">":
        keep = values > target
    elif operator == ">=":
        keep = values >= target
    elif operator == "=":
        keep = values.round(1).eq(round(target, 1))
    elif operator == "<=":
        keep = values <= target
    else:
        keep = values < target
    return data.loc[keep.fillna(False)]


def numeric_filter_control(
    data: pd.DataFrame,
    full_catalog: pd.DataFrame,
    label: str,
    column: str,
    key: str,
) -> pd.DataFrame:
    values = pd.to_numeric(full_catalog[column], errors="coerce").dropna()
    default = round(float(values.median()), 1)

    st.caption(label)
    operator_column, value_column = st.columns([0.85, 1.5])
    with operator_column:
        operator = st.selectbox(
            f"{label} comparison",
            OPERATORS,
            key=f"{key}_operator",
            label_visibility="collapsed",
        )
    with value_column:
        target = st.number_input(
            f"{label} value",
            value=default,
            step=0.1,
            format="%.1f",
            key=f"{key}_value",
            disabled=operator == "Any",
            label_visibility="collapsed",
        )
    return apply_numeric_filter(data, column, operator, float(target))


def short_value(value: object, suffix: str) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "NA"
    return f"{float(numeric):.1f}{suffix}"


def option_label(row: pd.Series) -> str:
    speed = short_value(row.get("attack_angle_contact_bat_speed_mph"), " mph")
    angle = short_value(row.get("attack_angle_contact_computed_deg"), " deg")
    return f"{row['session_swing']}  |  {speed}  |  {angle}"


viewers = discover_viewers()
if not viewers:
    st.error("No interactive swing viewer assets were found.")
    st.stop()

catalog = load_catalog(tuple(viewers))
if catalog.empty:
    st.error("Viewer assets were found, but none matched the processed swing table.")
    st.stop()

st.title("OBP Biomechanical Swing Viewer")
st.write(
    "Filter the complete swing dataset in the sidebar, choose one of the matching swings, "
    "then scrub through its motion from multiple angles and compare timing, force, segment "
    "velocity, bat path, and contact measurements."
)

with st.sidebar:
    st.header("Filter swings")

    side_values = sorted(
        value for value in catalog["hitter_side"].dropna().astype(str).unique()
    )
    selected_sides = st.multiselect(
        "Hitter side",
        side_values,
        default=side_values,
    )

    level_values = sorted(
        value
        for value in catalog["highest_playing_level"].dropna().astype(str).unique()
    )
    selected_levels = st.multiselect(
        "Playing level",
        level_values,
        default=level_values,
    )

    filtered = catalog.copy()
    if selected_sides:
        filtered = filtered[filtered["hitter_side"].astype(str).isin(selected_sides)]
    else:
        filtered = filtered.iloc[0:0]
    if selected_levels:
        filtered = filtered[
            filtered["highest_playing_level"].astype(str).isin(selected_levels)
        ]
    else:
        filtered = filtered.iloc[0:0]

    st.divider()
    st.subheader("Swing metrics")
    for label, column, key in FILTER_DEFINITIONS:
        filtered = numeric_filter_control(
            filtered,
            catalog,
            label,
            column,
            key,
        )

    st.divider()
    st.caption(f"{len(filtered)} of {len(catalog)} swings match")

if filtered.empty:
    st.warning("No swings match the selected filters. Adjust one or more conditions.")
    st.stop()

swing_ids = filtered["session_swing"].tolist()
query_swing = st.query_params.get("swing")
if (
    "swing_selector" not in st.session_state
    or st.session_state.swing_selector not in swing_ids
):
    st.session_state.swing_selector = (
        query_swing if query_swing in swing_ids else swing_ids[0]
    )

label_lookup = {
    row["session_swing"]: option_label(row)
    for _, row in filtered.iterrows()
}
with st.sidebar:
    selected_id = st.selectbox(
        "Matching swing",
        swing_ids,
        key="swing_selector",
        format_func=lambda value: label_lookup[value],
    )

st.query_params["swing"] = selected_id
selected = catalog.loc[catalog["session_swing"].eq(selected_id)].iloc[0]

viewer_path = viewers[selected_id]
viewer_html = read_viewer(str(viewer_path), viewer_path.stat().st_mtime_ns)
st.iframe(viewer_html, height=1120)

with st.expander("Swing data details"):
    detail_fields = (
        ("Swing ID", "session_swing", "{}"),
        ("Athlete ID", "user", "{:.0f}"),
        ("Hitter side", "hitter_side", "{}"),
        ("Highest playing level", "highest_playing_level", "{}"),
        ("Bat speed", "attack_angle_contact_bat_speed_mph", "{:.1f} mph"),
        ("Attack angle", "attack_angle_contact_computed_deg", "{:.1f} deg"),
        ("Swing length", "swing_length_from_barrel_inflection_in", "{:.1f} in"),
        ("Ideal zone time", "attack_zone_time_ms", "{:.1f} ms"),
        (
            "Attack direction at contact",
            "attack_direction_contact_pull_deg",
            "{:.1f} deg",
        ),
        ("Ideal-zone share of swing", "attack_zone_pct_of_swing", "{:.1f}%"),
        ("Ideal-zone depth range", "attack_zone_depth_range_in", "{:.1f} in"),
        ("Exit velocity", "exit_velo_mph_x", "{:.1f} mph"),
    )
    detail_rows = []
    for label, field, template in detail_fields:
        value = selected.get(field)
        if pd.isna(value):
            display = "Not available"
        elif any(token in template for token in (".0f", ".1f")):
            display = template.format(float(value))
        else:
            display = template.format(value)
        detail_rows.append({"Measurement": label, "Value": display})
    st.dataframe(
        pd.DataFrame(detail_rows),
        hide_index=True,
        width="stretch",
    )
