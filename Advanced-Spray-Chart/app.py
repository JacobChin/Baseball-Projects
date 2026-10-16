from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


DATA_PATH = Path(__file__).parent / "data" / "statcast_bbe_2024_2026.parquet"
HIT_EVENTS = {"single", "double", "triple", "home_run"}
OUT_EVENTS = {
    "field_out", "force_out", "grounded_into_double_play", "double_play",
    "fielders_choice_out", "fielders_choice", "other_out",
}
ZONE_MIRROR = {
    1: 3, 3: 1, 4: 6, 6: 4, 7: 9, 9: 7,
    11: 12, 12: 11, 13: 14, 14: 13, 2: 2, 5: 5, 8: 8,
}
RESULT_GROUPS = [
    "All", "Hits", "Outs", "Home Runs", "Extra-Base Hits", "Non-HR",
    "Ground Balls", "Line Drives", "Fly Balls", "Popups",
]
METRICS = {
    "BA": ("ba", None, 3),
    "xBA": ("mean", "estimated_ba_using_speedangle", 3),
    "xWOBA": ("mean", "estimated_woba_using_speedangle", 3),
    "Avg EV": ("mean", "launch_speed", 1),
    "EV50": ("ev50", "launch_speed", 1),
    "Median LA": ("median", "launch_angle", 1),
    "Contact Out In Front": ("median", "intercept_ball_minus_batter_pos_y_inches", 1),
    "Attack Angle": ("median", "attack_angle", 1),
    "Attack Direction": ("median", "attack_direction", 1),
    "Swing Path Tilt": ("median", "swing_path_tilt", 1),
    "Bat Speed": ("median", "bat_speed", 1),
    "Swing Length": ("median", "swing_length", 1),
    "Squared-Up Rate": ("squared", None, 1),
}


st.set_page_config(page_title="Advanced Spray Chart", page_icon="⚾", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.1rem; max-width: 1500px;}
    [data-testid="stMetric"] {border: 1px solid #2d333b; padding: 10px 12px; border-radius: 6px;}
    [data-testid="stSidebar"] {min-width: 310px; max-width: 310px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading 2024-2026 batted-ball data...")
def load_data(path: Path) -> pd.DataFrame:
    data = pd.read_parquet(path)
    numeric_cols = [
        "batter", "balls", "strikes", "zone", "game_year", "hc_x", "hc_y",
        "hit_distance_sc", "launch_speed", "launch_angle", "release_speed",
        "estimated_ba_using_speedangle", "estimated_woba_using_speedangle",
        "bat_speed", "swing_length", "attack_angle", "attack_direction",
        "swing_path_tilt", "intercept_ball_minus_batter_pos_y_inches",
    ]
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    return data


def apply_result_filter(data: pd.DataFrame, result: str) -> pd.DataFrame:
    if result == "Hits":
        return data[data["events"].isin(HIT_EVENTS)]
    if result == "Outs":
        return data[data["events"].isin(OUT_EVENTS)]
    if result == "Home Runs":
        return data[data["events"].eq("home_run")]
    if result == "Extra-Base Hits":
        return data[data["events"].isin({"double", "triple", "home_run"})]
    if result == "Non-HR":
        return data[~data["events"].eq("home_run")]
    bb_map = {
        "Ground Balls": "ground_ball", "Line Drives": "line_drive",
        "Fly Balls": "fly_ball", "Popups": "popup",
    }
    if result in bb_map:
        return data[data["bb_type"].eq(bb_map[result])]
    return data


def add_tracking_fields(data: pd.DataFrame, threshold: float) -> pd.DataFrame:
    out = data.copy()
    raw_angle = np.degrees(np.arctan2(out["hc_x"] - 125.42, 198.27 - out["hc_y"]))
    out["spray_angle"] = raw_angle
    out["normalized_spray_angle"] = np.where(out["stand"].eq("L"), -raw_angle, raw_angle)
    max_ev = 1.23 * out["bat_speed"] + 0.23 * (0.92 * out["release_speed"])
    out["squared_up_pct"] = out["launch_speed"] / max_ev.where(max_ev.gt(0))
    out["is_squared_up"] = out["squared_up_pct"].ge(threshold / 100).where(out["squared_up_pct"].notna())
    return out


def parse_zones(text: str) -> list[int] | None:
    if not text.strip():
        return None
    try:
        return sorted({int(value.strip()) for value in text.split(",") if value.strip()})
    except ValueError:
        st.sidebar.error("Zones must be comma-separated numbers, such as 3,6,9.")
        return None


def filter_data(
    data: pd.DataFrame,
    seasons: list[int],
    balls: list[int],
    strikes: list[int],
    pitch_group: str,
    pitch_name: str,
    zones: list[int] | None,
    pitcher_throws: str,
    result: str,
    spray_range: tuple[int, int],
    squared_threshold: float,
    squared_mode: str,
    squared_filter_pct: float,
    player: str | None = None,
) -> pd.DataFrame:
    out = data[data["game_year"].isin(seasons)].copy()
    if player:
        out = out[out["batter_name"].str.casefold().eq(player.casefold())]
    if balls:
        out = out[out["balls"].isin(balls)]
    if strikes:
        out = out[out["strikes"].isin(strikes)]
    if pitch_group != "All":
        out = out[out["pitch_bucket"].eq(pitch_group)]
    if pitch_name != "All":
        out = out[out["pitch_name"].eq(pitch_name)]
    if pitcher_throws != "All":
        out = out[out["p_throws"].eq(pitcher_throws)]
    if zones:
        left = set(zones)
        right = {ZONE_MIRROR.get(zone, zone) for zone in left}
        out = out[(out["stand"].eq("L") & out["zone"].isin(left)) | (out["stand"].eq("R") & out["zone"].isin(right))]
    out = apply_result_filter(out, result)
    out = out.dropna(subset=["hc_x", "hc_y", "hit_distance_sc"])
    out = add_tracking_fields(out, squared_threshold)
    out = out[out["normalized_spray_angle"].between(*spray_range, inclusive="both")]
    if squared_mode == "Over or equal":
        out = out[out["squared_up_pct"].ge(squared_filter_pct / 100)]
    elif squared_mode == "Under or equal":
        out = out[out["squared_up_pct"].le(squared_filter_pct / 100)]
    return out


def ev50(values: pd.Series) -> float:
    valid = pd.to_numeric(values, errors="coerce").dropna().sort_values(ascending=False)
    return valid.head(int(np.ceil(len(valid) / 2))).mean() if len(valid) else np.nan


def spray_figure(data: pd.DataFrame, player: str, subtitle: list[str]) -> go.Figure:
    out = data.copy()
    angle = np.radians(out["spray_angle"])
    out["field_x"] = out["hit_distance_sc"] * np.sin(angle)
    out["field_y"] = out["hit_distance_sc"] * np.cos(angle)
    colors = {"ground_ball": "#7568ef", "line_drive": "#54c2df", "fly_ball": "#ef476f", "popup": "#7bd88f"}
    labels = {"ground_ball": "Ground Ball", "line_drive": "Line Drive", "fly_ball": "Fly Ball", "popup": "Popup"}

    fig = go.Figure()
    theta = np.linspace(-45, 45, 220)
    fence = 400
    fig.add_trace(go.Scatter(x=fence * np.sin(np.radians(theta)), y=fence * np.cos(np.radians(theta)), mode="lines", name="Outfield Fence", line=dict(color="#5794ff", width=3)))
    for sign, color in [(-1, "#ff684d"), (1, "#23e6c5")]:
        fig.add_trace(go.Scatter(x=[0, sign * 300 * np.sin(np.radians(45))], y=[0, 300 * np.cos(np.radians(45))], mode="lines", showlegend=False, line=dict(color=color, width=2, dash="dash")))
    dirt_theta = np.linspace(-45, 45, 120)
    fig.add_trace(go.Scatter(x=95 * np.sin(np.radians(dirt_theta)), y=95 * np.cos(np.radians(dirt_theta)), mode="lines", name="Infield Dirt", line=dict(color="#a855f7", width=2)))

    for bb_type in ["ground_ball", "line_drive", "fly_ball", "popup"]:
        part = out[out["bb_type"].eq(bb_type)]
        if part.empty:
            continue
        custom = np.column_stack([
            part["batter_name"], part["balls"], part["strikes"], part["pitch_name"], part["zone"],
            part["launch_speed"], part["launch_angle"], part["hit_distance_sc"],
            part["estimated_ba_using_speedangle"], part["estimated_woba_using_speedangle"],
            part["squared_up_pct"] * 100, part["bat_speed"], part["swing_length"],
        ])
        fig.add_trace(go.Scatter(
            x=part["field_x"], y=part["field_y"], mode="markers", name=labels[bb_type], customdata=custom,
            marker=dict(color=colors[bb_type], size=part["launch_speed"].div(5).clip(6, 18).fillna(8), opacity=.82, line=dict(width=.7, color="white")),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>Count: %{customdata[1]}-%{customdata[2]}<br>"
                "Pitch: %{customdata[3]}<br>Zone: %{customdata[4]}<br>EV: %{customdata[5]:.1f} mph<br>"
                "LA: %{customdata[6]:.1f}°<br>Distance: %{customdata[7]:.0f} ft<br>xBA: %{customdata[8]:.3f}<br>"
                "xWOBA: %{customdata[9]:.3f}<br>Squared-Up: %{customdata[10]:.1f}%<br>"
                "Bat Speed: %{customdata[11]:.1f} mph<br>Swing Length: %{customdata[12]:.1f} ft<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="<br>".join([f"{player} Spray Chart", *subtitle]), height=760,
        margin=dict(l=10, r=10, t=120, b=10), paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(color="#e6edf3"), legend=dict(title="Batted Ball Type", bgcolor="rgba(255,255,255,.93)", font=dict(color="#446")),
        hoverlabel=dict(font_color="black"),
        xaxis=dict(range=[-350, 350], visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(range=[-25, 430], visible=False),
    )
    return fig


def metric_table(data: pd.DataFrame, metric: str, min_bbes: int) -> pd.DataFrame:
    grouped = data.groupby(["batter", "batter_name", "stand"], dropna=False)
    table = grouped.size().rename("batted_balls").reset_index()
    kind, column, decimals = METRICS[metric]
    keys = ["batter", "batter_name", "stand"]
    if kind == "ba":
        hits = grouped["events"].apply(lambda values: values.isin(HIT_EVENTS).sum()).rename("hits").reset_index()
        outs = grouped["events"].apply(lambda values: values.isin(OUT_EVENTS).sum()).rename("outs").reset_index()
        table = table.merge(hits, on=keys).merge(outs, on=keys)
        table["ab"] = table["hits"] + table["outs"]
        table[metric] = table["hits"] / table["ab"].replace(0, np.nan)
    elif kind == "mean":
        values = grouped[column].mean().rename(metric).reset_index()
        table = table.merge(values, on=keys)
    elif kind == "median":
        values = grouped[column].median().rename(metric).reset_index()
        table = table.merge(values, on=keys)
    elif kind == "ev50":
        values = grouped[column].apply(ev50).rename(metric).reset_index()
        table = table.merge(values, on=keys)
    elif kind == "squared":
        values = grouped["is_squared_up"].agg(["mean", "count"]).reset_index().rename(columns={"mean": metric, "count": "valid_squared_up_bbes"})
        values[metric] *= 100
        table = table.merge(values, on=keys)
        table = table[table["valid_squared_up_bbes"].ge(min_bbes)]
    table = table[table["batted_balls"].ge(min_bbes) & table[metric].notna()].copy()
    table[metric] = table[metric].round(decimals)
    return table


def composite_table(data: pd.DataFrame, choices: list[str], min_bbes: int) -> pd.DataFrame:
    base = data.groupby(["batter", "batter_name", "stand"], dropna=False).size().rename("batted_balls").reset_index()
    base = base[base["batted_balls"].ge(min_bbes)].copy()
    keys = ["batter", "batter_name", "stand"]
    percentile_cols = []
    for choice in choices:
        metric, direction = choice.rsplit(" · ", 1)
        values = metric_table(data, metric, min_bbes)[keys + [metric]]
        base = base.merge(values, on=keys, how="inner")
        pct_col = f"{metric} %ile ({direction})"
        base[pct_col] = base[metric].rank(pct=True, ascending=direction == "high") * 100
        percentile_cols.append(pct_col)
    base["Composite Percentile"] = base[percentile_cols].mean(axis=1, skipna=False)
    for col in ["Composite Percentile", *percentile_cols]:
        base[col] = base[col].round(1)
    return base[[*keys, "batted_balls", "Composite Percentile", *percentile_cols]]


if not DATA_PATH.exists():
    st.error(f"App data is missing: {DATA_PATH}. Run `python prepare_data.py` first.")
    st.stop()

df = load_data(DATA_PATH)
available_years = sorted(df["game_year"].dropna().astype(int).unique().tolist())

st.title("Advanced Spray Chart")
st.caption("Explore hitter contact quality across the 2024-2026 seasons.")

with st.sidebar:
    st.header("Filters")
    seasons = st.multiselect("Season", available_years, default=available_years)
    player_options = sorted(df.loc[df["game_year"].isin(seasons), "batter_name"].dropna().unique().tolist())
    player = st.selectbox("Batter", player_options, index=0 if player_options else None)
    balls = st.multiselect("Balls", [0, 1, 2, 3], default=[0, 1, 2, 3])
    strikes = st.multiselect("Strikes", [0, 1, 2], default=[0, 1, 2])
    pitch_group = st.selectbox("Pitch Group", ["All", "Fastball", "Breaking", "Offspeed"])
    pitch_names = ["All"] + sorted(df["pitch_name"].dropna().unique().tolist())
    pitch_name = st.selectbox("Pitch Type", pitch_names)
    zones_text = st.text_input("Zones (lefty perspective)", placeholder="Example: 3,6,9")
    zones = parse_zones(zones_text)
    pitcher_throws = st.selectbox("Pitcher Throws", ["All", "R", "L"])
    result = st.selectbox("Result", RESULT_GROUPS)
    spray_range = st.slider("Spray Angle", -45, 45, (-45, 45))
    squared_threshold = st.number_input("Squared-Up Definition %", 0.0, 120.0, 80.0, 1.0)
    squared_mode = st.selectbox("Squared-Up Point Filter", ["All", "Over or equal", "Under or equal"])
    squared_filter_pct = st.number_input("Squared-Up Filter %", 0.0, 120.0, 80.0, 1.0, disabled=squared_mode == "All")

filtered_all = filter_data(
    df, seasons, balls, strikes, pitch_group, pitch_name, zones, pitcher_throws,
    result, spray_range, squared_threshold, squared_mode, squared_filter_pct,
)

spray_tab, leaderboard_tab = st.tabs(["Spray Chart", "Leaderboard"])

with spray_tab:
    player_data = filtered_all[filtered_all["batter_name"].eq(player)].copy()
    if player_data.empty:
        st.info("No batted balls match these filters for this player.")
    else:
        subtitle = [f"Seasons: {', '.join(map(str, seasons))}", f"Batted balls: {len(player_data):,}"]
        if pitch_group != "All": subtitle.append(f"Pitch Group: {pitch_group}")
        if squared_mode != "All": subtitle.append(f"Squared-Up %: {squared_mode} {squared_filter_pct:.0f}%")
        fig = spray_figure(player_data, player, subtitle)
        st.plotly_chart(fig, use_container_width=True)
        hits = player_data["events"].isin(HIT_EVENTS).sum()
        outs = player_data["events"].isin(OUT_EVENTS).sum()
        ab = hits + outs
        metrics = [
            ("BBEs", f"{len(player_data):,}"),
            ("BA", f"{hits / ab:.3f}" if ab else "N/A"),
            ("xBA", f"{player_data['estimated_ba_using_speedangle'].mean():.3f}"),
            ("xWOBA", f"{player_data['estimated_woba_using_speedangle'].mean():.3f}"),
            ("EV50", f"{ev50(player_data['launch_speed']):.1f}"),
            ("Median LA", f"{player_data['launch_angle'].median():.1f}°"),
            ("Squared-Up Rate", f"{player_data['is_squared_up'].mean() * 100:.1f}%"),
        ]
        columns = st.columns(len(metrics))
        for column, (label, value) in zip(columns, metrics):
            column.metric(label, value)
        st.download_button("Download interactive chart", fig.to_html(include_plotlyjs="cdn"), file_name=f"{player.replace(' ', '_')}_spray_chart.html", mime="text/html")

with leaderboard_tab:
    top_controls = st.columns([1.4, 1, 1])
    metric = top_controls[0].selectbox("Metric", [*METRICS, "Composite Percentile"])
    min_bbes = top_controls[1].number_input("Minimum BBEs", 1, 1000, 25)
    rows = top_controls[2].number_input("Rows", 1, 100, 15)
    composite_choices = []
    if metric == "Composite Percentile":
        options = [f"{name} · {direction}" for name in METRICS for direction in ("high", "low")]
        composite_choices = st.multiselect("Composite AND metrics", options, default=["xWOBA · high", "Squared-Up Rate · high"])
        if not composite_choices:
            st.info("Choose at least one composite metric.")
            st.stop()
        table = composite_table(filtered_all, composite_choices, int(min_bbes))
    else:
        table = metric_table(filtered_all, metric, int(min_bbes))

    if table.empty:
        st.info("No players match these filters and minimum batted balls.")
    else:
        score_col = metric
        high = table.sort_values([score_col, "batted_balls"], ascending=[False, False]).reset_index(drop=True)
        low = table.sort_values([score_col, "batted_balls"], ascending=[True, False]).reset_index(drop=True)
        high.insert(0, "rank", np.arange(1, len(high) + 1))
        low.insert(0, "rank", np.arange(1, len(low) + 1))
        lookup = st.text_input("Find a player in the current leaderboard", placeholder="Type part of a name")
        if lookup:
            matches = high[high["batter_name"].str.contains(lookup, case=False, na=False)]
            st.dataframe(matches, hide_index=True, use_container_width=True)
        left, right = st.columns(2)
        left.subheader("Highest")
        left.dataframe(high.head(int(rows)), hide_index=True, use_container_width=True)
        right.subheader("Lowest")
        right.dataframe(low.head(int(rows)), hide_index=True, use_container_width=True)
        csv = high.to_csv(index=False).encode("utf-8")
        st.download_button("Download full leaderboard CSV", csv, "advanced_spray_leaderboard.csv", "text/csv")
