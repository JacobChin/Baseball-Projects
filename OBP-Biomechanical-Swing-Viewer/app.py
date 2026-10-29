from __future__ import annotations

import gzip
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


ROOT = Path(__file__).resolve().parent
METRICS_PATH = ROOT / "outputs" / "attack_angle_zone_metrics.csv"
MANIFEST_PATH = ROOT / "outputs" / "swing_manifest.csv"
VIEWER_DIRS = (ROOT / "outputs" / "qc_viewers", ROOT / "Viewer-Examples")
IGNORED_VIEWERS = {"index", "definitions"}

DISPLAY_METRICS = (
    ("Bat speed", "attack_angle_contact_bat_speed_mph", "{:.1f} mph"),
    ("Attack angle", "attack_angle_contact_x", "{:.1f} deg"),
    ("Ideal-zone time", "attack_zone_time_ms", "{:.1f} ms"),
    ("Swing length", "swing_length_from_barrel_inflection_in", "{:.1f} in"),
    ("Contact out front", "contact_barrel_x_relative_com_in", "{:.1f} in"),
    ("Swing path tilt", "swing_path_tilt_contact_deg", "{:.1f} deg"),
)


st.set_page_config(
    page_title="OBP Biomechanical Swing Viewer",
    page_icon=":material/sports_baseball:",
    layout="wide",
)
st.markdown(
    """
    <style>
    .block-container {max-width: 1600px; padding-top: 1.25rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.7rem 0.85rem;
        min-height: 92px;
    }
    [data-testid="stMetricLabel"] {font-size: 0.82rem;}
    [data-testid="stMetricValue"] {font-size: 1.35rem;}
    [data-testid="stSidebar"] {min-width: 300px; max-width: 300px;}
    .viewer-note {color: #8b949e; font-size: 0.9rem; margin-top: -0.4rem;}
    @media (max-width: 768px) {
        h1 {font-size: 2.25rem !important;}
        div[data-testid="stHorizontalBlock"]:has([data-testid="stSelectbox"]) {
            display: grid;
            grid-template-columns: 44px minmax(0, 1fr) 44px;
            gap: 0.5rem;
        }
        div[data-testid="stHorizontalBlock"]:has([data-testid="stSelectbox"])
            > div[data-testid="stColumn"] {
            width: auto !important;
            min-width: 0 !important;
            flex: none !important;
        }
        div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.5rem;
        }
        div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
            > div[data-testid="stColumn"] {
            width: auto !important;
            min-width: 0 !important;
            flex: none !important;
        }
        [data-testid="stMetric"] {min-height: 84px; padding: 0.6rem 0.7rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _natural_swing_key(value: str) -> tuple[int, int, str]:
    try:
        session, swing = value.split("_", maxsplit=1)
        return int(session), int(swing), value
    except (TypeError, ValueError):
        return 10**9, 10**9, str(value)


def _viewer_id(path: Path) -> str:
    name = path.name
    if name.endswith(".html.gz"):
        return name[: -len(".html.gz")]
    return path.stem


@st.cache_data(show_spinner=False)
def discover_viewers() -> dict[str, Path]:
    viewers: dict[str, Path] = {}
    for directory in reversed(VIEWER_DIRS):
        if not directory.exists():
            continue
        for pattern in ("*.html", "*.html.gz"):
            for path in sorted(directory.glob(pattern)):
                swing_id = _viewer_id(path)
                if swing_id.lower() not in IGNORED_VIEWERS:
                    viewers[swing_id] = path
    return dict(sorted(viewers.items(), key=lambda item: _natural_swing_key(item[0])))


@st.cache_data(show_spinner="Loading swing measurements...")
def load_catalog(viewer_ids: tuple[str, ...]) -> pd.DataFrame:
    metrics = pd.read_csv(METRICS_PATH)
    manifest = pd.read_csv(MANIFEST_PATH)

    manifest_columns = [
        column
        for column in (
            "session_swing",
            "session_height_in",
            "athlete_age",
            "highest_playing_level",
            "hitter_side",
            "bat_weight_oz",
            "bat_length_in",
            "exit_velo_mph_x",
            "has_hittrax",
            "has_force",
        )
        if column in manifest.columns
    ]
    metric_columns = [
        column
        for column in (
            "session_swing",
            "user",
            "session",
            "highest_playing_level",
            "hitter_side",
            "attack_angle_contact_bat_speed_mph",
            "attack_angle_contact_x",
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

    catalog = metrics[metric_columns].copy()
    manifest_subset = manifest[manifest_columns].copy()
    duplicate_columns = set(catalog.columns) & set(manifest_subset.columns) - {"session_swing"}
    manifest_subset = manifest_subset.drop(columns=list(duplicate_columns), errors="ignore")
    catalog = catalog.merge(manifest_subset, on="session_swing", how="left")
    catalog["session_swing"] = catalog["session_swing"].astype(str)
    catalog = catalog[catalog["session_swing"].isin(viewer_ids)].copy()
    catalog["viewer_order"] = catalog["session_swing"].map(
        {swing_id: index for index, swing_id in enumerate(viewer_ids)}
    )
    return catalog.sort_values("viewer_order").reset_index(drop=True)


@st.cache_data(show_spinner="Opening interactive swing viewer...")
def read_viewer(path_string: str, modified_ns: int) -> str:
    del modified_ns
    path = Path(path_string)
    if path.name.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8")


def format_metric(value: object, template: str) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "Not available"
    return template.format(float(numeric))


def option_label(row: pd.Series) -> str:
    side = str(row.get("hitter_side", "")).upper()
    level = str(row.get("highest_playing_level", "Unknown"))
    return f"{row['session_swing']}  |  {side}HH  |  {level}"


def change_swing(swing_ids: list[str], offset: int) -> None:
    current = st.session_state.swing_selector
    index = swing_ids.index(current)
    st.session_state.swing_selector = swing_ids[(index + offset) % len(swing_ids)]


viewers = discover_viewers()
if not viewers:
    st.error("No interactive swing viewer files were found.")
    st.stop()

catalog = load_catalog(tuple(viewers))
if catalog.empty:
    st.error("Viewer files were found, but none matched the processed swing tables.")
    st.stop()

st.title("OBP Biomechanical Swing Viewer")
st.write(
    "Choose a swing to inspect its biomechanical summary, then use the interactive "
    "viewer to scrub through the motion from multiple angles and compare timing, force, "
    "segment velocity, bat path, and contact measurements."
)

with st.sidebar:
    st.header("Find a swing")
    search = st.text_input("Search swing ID", placeholder="Example: 180_1")

    side_values = sorted(value for value in catalog["hitter_side"].dropna().astype(str).unique())
    selected_sides = st.multiselect("Hitter side", side_values, default=side_values)

    level_values = sorted(
        value for value in catalog["highest_playing_level"].dropna().astype(str).unique()
    )
    selected_levels = st.multiselect("Playing level", level_values, default=level_values)

    qc_only = st.checkbox("Model-ready swings only", value=False)

    filtered = catalog.copy()
    if search:
        filtered = filtered[
            filtered["session_swing"].str.contains(search.strip(), case=False, regex=False)
        ]
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
    if qc_only and "model_ready_primary" in filtered.columns:
        filtered = filtered[filtered["model_ready_primary"].fillna(False).astype(bool)]

    st.caption(f"{len(filtered)} of {len(catalog)} available viewers")

if filtered.empty:
    st.warning("No available swing viewers match those filters.")
    st.stop()

swing_ids = filtered["session_swing"].tolist()
query_swing = st.query_params.get("swing")
if "swing_selector" not in st.session_state or st.session_state.swing_selector not in swing_ids:
    st.session_state.swing_selector = query_swing if query_swing in swing_ids else swing_ids[0]

control_left, control_middle, control_right = st.columns([1, 8, 1])
with control_left:
    st.button(
        "←",
        help="Previous swing",
        width="stretch",
        on_click=change_swing,
        args=(swing_ids, -1),
    )
with control_middle:
    label_lookup = {
        row["session_swing"]: option_label(row) for _, row in filtered.iterrows()
    }
    selected_id = st.selectbox(
        "Swing",
        swing_ids,
        key="swing_selector",
        format_func=lambda value: label_lookup[value],
        label_visibility="collapsed",
    )
with control_right:
    st.button(
        "→",
        help="Next swing",
        width="stretch",
        on_click=change_swing,
        args=(swing_ids, 1),
    )

st.query_params["swing"] = selected_id
selected = catalog.loc[catalog["session_swing"].eq(selected_id)].iloc[0]

metric_columns = st.columns(len(DISPLAY_METRICS))
for column, (label, field, template) in zip(metric_columns, DISPLAY_METRICS):
    column.metric(label, format_metric(selected.get(field), template))

metadata = []
if pd.notna(selected.get("user")):
    metadata.append(f"Athlete {int(selected['user'])}")
if pd.notna(selected.get("hitter_side")):
    metadata.append(f"{selected['hitter_side']}HH")
if pd.notna(selected.get("highest_playing_level")):
    metadata.append(str(selected["highest_playing_level"]))
if pd.notna(selected.get("attack_angle_qc")):
    metadata.append(f"Attack-angle QC: {selected['attack_angle_qc']}")
st.markdown(
    f"<p class='viewer-note'>Swing {selected_id} &nbsp;|&nbsp; "
    + " &nbsp;|&nbsp; ".join(metadata)
    + "</p>",
    unsafe_allow_html=True,
)

viewer_path = viewers[selected_id]
viewer_html = read_viewer(str(viewer_path), viewer_path.stat().st_mtime_ns)
st.iframe(viewer_html, height=1120)

with st.expander("Swing data details"):
    detail_fields = (
        ("Swing ID", "session_swing", "{}"),
        ("Athlete ID", "user", "{:.0f}"),
        ("Hitter side", "hitter_side", "{}"),
        ("Highest playing level", "highest_playing_level", "{}"),
        ("Attack direction at contact", "attack_direction_contact_pull_deg", "{:.1f} deg"),
        ("Ideal-zone share of swing", "attack_zone_pct_of_swing", "{:.1f}%"),
        ("Ideal-zone depth range", "attack_zone_depth_range_in", "{:.1f} in"),
        ("Exit velocity", "exit_velo_mph_x", "{:.1f} mph"),
        ("Bat length", "bat_length_in", "{:.1f} in"),
        ("Bat weight", "bat_weight_oz", "{:.1f} oz"),
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
    st.dataframe(pd.DataFrame(detail_rows), hide_index=True, width="stretch")

st.caption(
    "The app lists interactive viewer files included with the project. Additional HTML or "
    "HTML.GZ viewers placed in outputs/qc_viewers are discovered automatically."
)
