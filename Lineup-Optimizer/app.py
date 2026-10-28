"""Interactive lineup simulator app."""

from __future__ import annotations

import importlib
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

import baseball_lineup_optimizer.data.baseball_reference as baseball_reference_importer
from baseball_lineup_optimizer.engine.evaluator import attach_stolen_base_rates, profiles_from_rows
from baseball_lineup_optimizer.engine.lineup_optimizer import optimize_lineup_order
from baseball_lineup_optimizer.engine.outcomes import HitterProfile
from baseball_lineup_optimizer.engine.plan_engine import PlanEngineConfig, expected_one_run_probability_plan, expected_runs_plan, transition_model_summary
from baseball_lineup_optimizer.experiments.orderings import lineup_names


APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent if (APP_ROOT.parent / "baseball_lineup_optimizer").exists() else APP_ROOT
DATA_DIR = PROJECT_ROOT / "data" / "processed"
PLAYER_POOL_PATH = DATA_DIR / "player_pool_2025.csv"
POSITION_ELIGIBILITY_PATH = DATA_DIR / "position_eligibility_2025.csv"
STOLEN_BASE_RATES_PATH = DATA_DIR / "contextual_stolen_base_rates_2025.csv"
TRANSITION_MODEL_PATH = DATA_DIR / "transition_models_2021_2025_direct_movement.json"
SPEED_ATTEMPT_MODEL_PATH = DATA_DIR / "speed_attempt_models_2021_2025_direct_movement.json"
CONTEXTUAL_WALK_MODEL_PATH = DATA_DIR / "contextual_walk_model_2025.json"
DEFAULT_GAMES = 1_000


st.set_page_config(page_title="Lineup Optimizer", layout="wide")


@st.cache_data
def _load_pool(path: str, stolen_base_rates_path: str) -> pd.DataFrame:
    pool = pd.read_csv(path, encoding="utf-8")
    return attach_stolen_base_rates(pool, rates_path=stolen_base_rates_path)


@st.cache_data
def _load_position_eligibility(path: str) -> pd.DataFrame:
    eligibility_path = Path(path)
    if not eligibility_path.exists():
        return pd.DataFrame()
    data = pd.read_csv(eligibility_path)
    data["player_id"] = data["player_id"].astype(str)
    return data


def main() -> None:
    _init_state()
    pool = _load_pool(str(PLAYER_POOL_PATH), str(STOLEN_BASE_RATES_PATH))
    position_eligibility = _load_position_eligibility(str(POSITION_ELIGIBILITY_PATH))

    st.title("Lineup Optimizer")
    model_summary = transition_model_summary(
        PlanEngineConfig(
            use_empirical_transitions=True,
            transition_model_path=str(TRANSITION_MODEL_PATH),
        )
    )
    if model_summary.get("loaded"):
        st.caption(
            "Plan empirical engine: PA-level 9-inning offense with 2025 Statcast joint transitions, "
            "player-shrunk single/GB/flyout details, IBB/SH removed when available, no WP/PB/errors."
        )
    else:
        st.caption(
            "Plan engine fallback: PA-level 9-inning offense, IBB/SH removed when available, "
            "distinct GB/FB/LD/popup outs, no WP/PB/errors."
        )

    with st.sidebar:
        st.header("Simulation")
        games = st.slider("Simulation games", min_value=250, max_value=5_000, value=DEFAULT_GAMES, step=250)
        optimize_games = st.slider("Optimize games per order", min_value=50, max_value=1_000, value=250, step=50)
        random_orders = st.slider("Random orders to test", min_value=0, max_value=250, value=50, step=10)
        seed = st.number_input("Seed", min_value=1, max_value=9_999_999, value=202503, step=1)
        use_contextual_walks = st.checkbox("Use contextual BB model", value=True)
        _render_model_status(model_summary)

    picker_col, lineup_col = st.columns([1.05, 1.35], gap="large")
    with picker_col:
        _render_player_picker(pool)
        st.divider()
        _render_custom_hitter_form(pool, position_eligibility)

    with lineup_col:
        lineup = _render_lineup()
        st.divider()
        _render_simulation_actions(lineup, games, optimize_games, random_orders, int(seed), use_contextual_walks)


def _render_model_status(model_summary: dict[str, object]) -> None:
    with st.expander("Model status", expanded=False):
        if not model_summary.get("loaded"):
            st.warning("Empirical transition model not found; using transparent fallback constants.")
            return
        st.success(f"Loaded {int(model_summary.get('season', 0))} Statcast transition model")
        st.write(
            {
                "transition_keys": model_summary.get("transition_keys"),
                "transition_rows": model_summary.get("transition_rows"),
                "hitter_secondary_profiles": model_summary.get("hitter_profiles"),
                "secondary_distributions": model_summary.get("league_distributions"),
            }
        )
        st.caption("Sprint Speed drives runner advancement weighting; Home-to-First is preferred for batter-runner double-play weighting.")


def _init_state() -> None:
    st.session_state.setdefault("lineup_rows", [])
    st.session_state.setdefault("custom_hitters", [])
    st.session_state.setdefault("custom_form_defaults", _default_custom_hitter_values())
    st.session_state.custom_form_defaults = {
        **_default_custom_hitter_values(),
        **st.session_state.custom_form_defaults,
    }
    st.session_state.setdefault("custom_form_version", 0)
    st.session_state.setdefault("last_import_summary", "")


def _default_custom_hitter_values() -> dict[str, object]:
    return {
        "name": "Custom Hitter",
        "pa": 600,
        "ab": 520,
        "single": 80,
        "double": 30,
        "triple": 2,
        "hr": 35,
        "bb": 80,
        "hbp": 5,
        "k": 140,
        "sb": 5,
        "cs": 2,
        "rdp": 0.0,
        "ibb": 0,
        "sf": 0,
        "sh": 0,
        "sprint_speed": 27.0,
        "home_to_first": 4.35,
        "gb_rate": 0.42,
        "fb_rate": 0.38,
        "ld_rate": 0.20,
        "popup_rate": 0.05,
        "c_games": 0,
        "first_base_games": 0,
        "second_base_games": 0,
        "third_base_games": 0,
        "shortstop_games": 0,
        "outfield_games": 0,
        "source_player_id": "",
        "source_mlbam_id": "",
        "source_woba": 0.0,
        "source_wrc_plus": 100.0,
        "source_pa": 0,
        "source_ab": 0,
        "source_single": 0,
        "source_double": 0,
        "source_triple": 0,
        "source_hr": 0,
        "source_bb": 0,
        "source_hbp": 0,
        "source_k": 0
    }


def _render_player_picker(pool: pd.DataFrame) -> None:
    st.subheader("Add season player")
    query = st.text_input("Search player", placeholder="Aaron Judge")
    filtered = pool
    if query:
        filtered = pool[pool["player_name"].str.contains(query, case=False, na=False)]
    filtered = filtered.head(50)

    if filtered.empty:
        st.info("No matching players.")
        return

    labels = {
        _player_label(row): index
        for index, row in filtered.iterrows()
    }
    selected_label = st.selectbox("Player", options=list(labels.keys()), label_visibility="collapsed")
    row = pool.loc[labels[selected_label]].to_dict()
    add_col, fill_col = st.columns(2)
    with add_col:
        add_player = st.button("Add player", use_container_width=True)
    with fill_col:
        fill_player = st.button("Fill all 9 slots", use_container_width=True)
    if add_player:
        st.session_state.lineup_rows.append(_lineup_entry(row.copy(), source="season"))
        st.rerun()
    if fill_player:
        st.session_state.lineup_rows = [_lineup_entry(row.copy(), source="season") for _ in range(9)]
        st.rerun()


def _render_custom_hitter_form(pool: pd.DataFrame, position_eligibility: pd.DataFrame) -> None:
    st.subheader("Create custom hitter")
    _render_season_player_importer(pool, position_eligibility)
    _render_baseball_reference_importer()

    defaults = st.session_state.custom_form_defaults
    version = st.session_state.custom_form_version
    with st.form("custom_hitter_form", clear_on_submit=False):
        name = st.text_input("Name", value=str(defaults["name"]), key=f"custom_name_{version}")
        col1, col2, col3 = st.columns(3)
        with col1:
            pa = st.number_input("PA", min_value=1, value=int(defaults["pa"]), key=f"custom_pa_{version}")
            ab = st.number_input("AB", min_value=1, value=int(defaults["ab"]), key=f"custom_ab_{version}")
            single = st.number_input("1B", min_value=0, value=int(defaults["single"]), key=f"custom_1b_{version}")
            double = st.number_input("2B", min_value=0, value=int(defaults["double"]), key=f"custom_2b_{version}")
        with col2:
            triple = st.number_input("3B", min_value=0, value=int(defaults["triple"]), key=f"custom_3b_{version}")
            hr = st.number_input("HR", min_value=0, value=int(defaults["hr"]), key=f"custom_hr_{version}")
            bb = st.number_input("BB", min_value=0, value=int(defaults["bb"]), key=f"custom_bb_{version}")
            hbp = st.number_input("HBP", min_value=0, value=int(defaults["hbp"]), key=f"custom_hbp_{version}")
        with col3:
            k = st.number_input("SO", min_value=0, value=int(defaults["k"]), key=f"custom_so_{version}")
            sb = st.number_input("SB", min_value=0, value=int(defaults["sb"]), key=f"custom_sb_{version}")
            cs = st.number_input("CS", min_value=0, value=int(defaults["cs"]), key=f"custom_cs_{version}")
            rdp = st.number_input("Rdp", value=float(defaults["rdp"]), step=0.5, key=f"custom_rdp_{version}")

        speed_col1, speed_col2 = st.columns(2)
        with speed_col1:
            sprint_speed = st.number_input("Sprint Speed", min_value=20.0, max_value=34.0, value=float(defaults["sprint_speed"]), step=0.1, key=f"custom_sprint_{version}")
        with speed_col2:
            home_to_first = st.number_input("Home-to-First", min_value=3.5, max_value=5.5, value=float(defaults["home_to_first"]), step=0.01, key=f"custom_h2f_{version}")

        batted_ball_col1, batted_ball_col2, batted_ball_col3 = st.columns(3)
        with batted_ball_col1:
            gb_rate = st.number_input("GB%", min_value=0.0, max_value=1.0, value=float(defaults["gb_rate"]), step=0.01, key=f"custom_gb_{version}")
        with batted_ball_col2:
            fb_rate = st.number_input("FB%", min_value=0.0, max_value=1.0, value=float(defaults["fb_rate"]), step=0.01, key=f"custom_fb_{version}")
        with batted_ball_col3:
            ld_rate = st.number_input("LD%", min_value=0.0, max_value=1.0, value=float(defaults["ld_rate"]), step=0.01, key=f"custom_ld_{version}")

        with st.expander("Model details", expanded=False):
            detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)
            with detail_col1:
                ibb = st.number_input("IBB", min_value=0, value=int(defaults["ibb"]), key=f"custom_ibb_{version}")
            with detail_col2:
                sf = st.number_input("SF", min_value=0, value=int(defaults["sf"]), key=f"custom_sf_{version}")
            with detail_col3:
                sh = st.number_input("SH", min_value=0, value=int(defaults["sh"]), key=f"custom_sh_{version}")
            with detail_col4:
                popup_rate = st.number_input("Popup%", min_value=0.0, max_value=1.0, value=float(defaults["popup_rate"]), step=0.01, key=f"custom_popup_{version}")

        save_col, add_col = st.columns(2)
        with save_col:
            save_submitted = st.form_submit_button("Save custom hitter", use_container_width=True)
        with add_col:
            add_submitted = st.form_submit_button("Add to lineup", use_container_width=True)

    if save_submitted or add_submitted:
        row = _custom_hitter_row(
            name=name,
            pa=pa,
            ab=ab,
            single=single,
            double=double,
            triple=triple,
            hr=hr,
            bb=bb,
            hbp=hbp,
            k=k,
            sb=sb,
            cs=cs,
            rdp=rdp,
            ibb=ibb,
            sf=sf,
            sh=sh,
            sprint_speed=sprint_speed,
            home_to_first=home_to_first,
            gb_rate=gb_rate,
            fb_rate=fb_rate,
            ld_rate=ld_rate,
            popup_rate=popup_rate,
            c_games=defaults["c_games"],
            first_base_games=defaults["first_base_games"],
            second_base_games=defaults["second_base_games"],
            third_base_games=defaults["third_base_games"],
            shortstop_games=defaults["shortstop_games"],
            outfield_games=defaults["outfield_games"],
            source_woba=defaults.get("source_woba", 0.0),
            source_wrc_plus=defaults.get("source_wrc_plus", 100.0),
            source_pa=defaults.get("source_pa", 0),
            source_ab=defaults.get("source_ab", 0),
            source_single=defaults.get("source_single", 0),
            source_double=defaults.get("source_double", 0),
            source_triple=defaults.get("source_triple", 0),
            source_hr=defaults.get("source_hr", 0),
            source_bb=defaults.get("source_bb", 0),
            source_hbp=defaults.get("source_hbp", 0),
            source_k=defaults.get("source_k", 0),
        )
        error = _validate_custom_hitter(row)
        if error:
            st.error(error)
        else:
            if save_submitted:
                st.session_state.custom_hitters.append(row)
            if add_submitted:
                st.session_state.lineup_rows.append(_lineup_entry(row, source="custom"))
            st.rerun()

    _render_saved_custom_hitters()


def _render_season_player_importer(pool: pd.DataFrame, position_eligibility: pd.DataFrame) -> None:
    with st.expander("Load from 2025 player pool"):
        query = st.text_input("Find 2025 player", placeholder="Aaron Judge", key="custom_pool_import_query")
        filtered = pool
        if query:
            filtered = pool[pool["player_name"].str.contains(query, case=False, na=False)]
        filtered = filtered.sort_values("woba", ascending=False).head(75)
        if filtered.empty:
            st.info("No matching 2025 players.")
            return

        labels = {_player_label(row): index for index, row in filtered.iterrows()}
        selected_label = st.selectbox("2025 player", options=list(labels.keys()), key="custom_pool_import_select")
        row = pool.loc[labels[selected_label]].to_dict()
        if st.button("Load player into custom form", use_container_width=True):
            imported_defaults = {
                **_default_custom_hitter_values(),
                **_season_player_form_defaults(row, position_eligibility),
            }
            st.session_state.custom_form_defaults = imported_defaults
            st.session_state.custom_form_version = int(st.session_state.custom_form_version) + 1
            st.session_state.last_import_summary = (
                f"Loaded {row['player_name']} {int(row.get('season', 2025))}: "
                f"wOBA {float(row.get('woba', 0.0)):.3f}, "
                f"HR {int(row.get('hr', 0))}, BB {int(row.get('bb', 0))}, SO {int(row.get('k', 0))}. "
                "Edit the fields below, then save or add the custom version."
            )
            st.rerun()
        if st.session_state.last_import_summary:
            st.caption(st.session_state.last_import_summary)

def _season_player_form_defaults(row: dict[str, object], position_eligibility: pd.DataFrame) -> dict[str, object]:
    player_id = str(row.get("player_id", ""))
    position_row = pd.Series(dtype=object)
    if not position_eligibility.empty and player_id:
        matches = position_eligibility[position_eligibility["player_id"].astype(str).eq(player_id)]
        if not matches.empty:
            position_row = matches.iloc[0]

    return {
        "name": f"{row.get('player_name', 'Custom Hitter')} {int(_number_or_default(row.get('season'), 2025))} custom",
        "pa": _int_or_default(row.get("pa"), 600),
        "ab": _int_or_default(row.get("ab"), 520),
        "single": _int_or_default(row.get("single"), 0),
        "double": _int_or_default(row.get("double"), 0),
        "triple": _int_or_default(row.get("triple"), 0),
        "hr": _int_or_default(row.get("hr"), 0),
        "bb": _int_or_default(row.get("bb"), 0),
        "hbp": _int_or_default(row.get("hbp"), 0),
        "k": _int_or_default(row.get("k"), 0),
        "sb": _int_or_default(row.get("sb"), 0),
        "cs": _int_or_default(row.get("cs"), 0),
        "rdp": _number_or_default(row.get("gdp_runs"), 0.0),
        "ibb": _int_or_default(row.get("ibb"), 0),
        "sf": _int_or_default(row.get("sf"), 0),
        "sh": _int_or_default(row.get("sh"), 0),
        "sprint_speed": _number_or_default(row.get("sprint_speed"), 27.0),
        "home_to_first": _number_or_default(row.get("home_to_first"), 4.35),
        "gb_rate": _number_or_default(row.get("gb_rate"), 0.42),
        "fb_rate": _number_or_default(row.get("fb_rate"), 0.38),
        "ld_rate": _number_or_default(row.get("ld_rate"), 0.20),
        "popup_rate": _number_or_default(row.get("popup_rate"), 0.05),
        "source_player_id": str(row.get("player_id", "")),
        "source_mlbam_id": str(row.get("mlbam_id", "")),
        "source_woba": _number_or_default(row.get("woba"), 0.0),
        "source_wrc_plus": _number_or_default(row.get("wrc_plus"), 100.0),
        "source_pa": _int_or_default(row.get("pa"), 0),
        "source_ab": _int_or_default(row.get("ab"), 0),
        "source_single": _int_or_default(row.get("single"), 0),
        "source_double": _int_or_default(row.get("double"), 0),
        "source_triple": _int_or_default(row.get("triple"), 0),
        "source_hr": _int_or_default(row.get("hr"), 0),
        "source_bb": _int_or_default(row.get("bb"), 0),
        "source_hbp": _int_or_default(row.get("hbp"), 0),
        "source_k": _int_or_default(row.get("k"), 0),
        "c_games": _int_or_default(position_row.get("c"), 0),
        "first_base_games": _int_or_default(position_row.get("1b"), 0),
        "second_base_games": _int_or_default(position_row.get("2b"), 0),
        "third_base_games": _int_or_default(position_row.get("3b"), 0),
        "shortstop_games": _int_or_default(position_row.get("ss"), 0),
        "outfield_games": _int_or_default(position_row.get("of"), 0),
    }

def _render_baseball_reference_importer() -> None:
    with st.expander("Import from Baseball-Reference"):
        url = st.text_input(
            "Player page URL",
            placeholder="https://www.baseball-reference.com/players/s/suzukic01.shtml",
        )
        season = st.number_input("Season", min_value=1871, max_value=2100, value=2004, step=1)
        if st.button("Import season into form", use_container_width=True):
            try:
                importlib.reload(baseball_reference_importer)
                imported = baseball_reference_importer.import_baseball_reference_hitter_season(url, int(season))
            except Exception as exc:
                st.error(f"Import failed: {exc}")
            else:
                imported_defaults = {
                    **_default_custom_hitter_values(),
                    **imported.as_form_defaults(),
                }
                st.session_state.custom_form_defaults = imported_defaults
                st.session_state.custom_form_version = int(st.session_state.custom_form_version) + 1
                st.session_state.last_import_summary = (
                    f"Imported {imported.name}: "
                    f"GB% {imported_defaults['gb_rate']:.3f}, "
                    f"FB% {imported_defaults['fb_rate']:.3f}, "
                    f"LD% {imported_defaults['ld_rate']:.3f}. "
                    "Savant Sprint/Home-to-First are used when available; historical custom hitters keep the entered defaults."
                )
                st.rerun()
        if st.session_state.last_import_summary:
            st.caption(st.session_state.last_import_summary)


def _render_saved_custom_hitters() -> None:
    saved_hitters = st.session_state.custom_hitters
    if not saved_hitters:
        st.caption("Saved custom hitters will appear here for this app session.")
        return

    st.markdown("**Saved custom hitters**")
    if st.button("Save custom hitters CSV", use_container_width=True):
        output_path = DATA_DIR / "custom_hitters_streamlit.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(saved_hitters).to_csv(output_path, index=False)
        st.success(f"Saved {len(saved_hitters)} custom hitters to {output_path}")
    for index, row in enumerate(saved_hitters):
        left, add_col, fill_col, remove_col = st.columns([0.48, 0.17, 0.22, 0.13])
        left.write(_saved_custom_label(row))
        if add_col.button("Add", key=f"add_custom_{row['player_id']}_{index}", use_container_width=True):
            st.session_state.lineup_rows.append(_lineup_entry(row.copy(), source="custom"))
            st.rerun()
        if fill_col.button("Fill 9", key=f"fill_custom_{row['player_id']}_{index}", use_container_width=True):
            st.session_state.lineup_rows = [_lineup_entry(row.copy(), source="custom") for _ in range(9)]
            st.rerun()
        if remove_col.button("X", key=f"remove_custom_{row['player_id']}_{index}", use_container_width=True):
            st.session_state.custom_hitters.pop(index)
            st.rerun()


def _render_lineup() -> list[HitterProfile]:
    st.subheader("Selected lineup")
    rows = st.session_state.lineup_rows
    if not rows:
        st.info("Add nine hitters to simulate an offense. Duplicates are allowed.")
        return []

    for index, entry in enumerate(rows):
        left, middle, right = st.columns([0.1, 0.75, 0.15])
        left.write(f"{index + 1}.")
        middle.write(_entry_label(entry))
        if right.button("Remove", key=f"remove_{entry['instance_id']}"):
            st.session_state.lineup_rows.pop(index)
            st.rerun()

    st.progress(min(len(rows), 9) / 9, text=f"{len(rows)} / 9 hitters selected")
    if len(rows) > 9:
        st.warning("Only exactly nine hitters can be simulated. Remove extra hitters.")
    if st.button("Clear lineup", use_container_width=True):
        st.session_state.lineup_rows = []
        st.rerun()

    return [HitterProfile.from_mapping(entry["row"]) for entry in rows] if len(rows) == 9 else []


def _render_simulation_actions(
    lineup: list[HitterProfile],
    games: int,
    optimize_games: int,
    random_orders: int,
    seed: int,
    use_contextual_walks: bool,
) -> None:
    st.subheader("Run")
    if len(lineup) != 9:
        st.button("Simulate selected order", disabled=True, use_container_width=True)
        st.button("Optimize batting order", disabled=True, use_container_width=True)
        return

    config = PlanEngineConfig(
        use_empirical_transitions=True,
        transition_model_path=str(TRANSITION_MODEL_PATH),
        use_contextual_walks=use_contextual_walks,
        contextual_walk_model_path=str(CONTEXTUAL_WALK_MODEL_PATH),
        runner_advancement_model="empirical_speed_attempt",
        speed_attempt_model_path=str(SPEED_ATTEMPT_MODEL_PATH),
    )
    sim_col, one_run_col, opt_col = st.columns(3)
    with sim_col:
        if st.button("Simulate selected order", use_container_width=True):
            with st.spinner("Simulating selected order..."):
                result = expected_runs_plan(lineup, games=games, seed=seed, innings_per_game=9, config=config)
            _show_result("Selected order", lineup, result.runs_per_game, result.run_std, result.games)

    with one_run_col:
        if st.button("One-run probability", use_container_width=True):
            with st.spinner("Simulating one-run innings..."):
                result = expected_one_run_probability_plan(lineup, trials=games, seed=seed, config=config)
            _show_one_run_result("One-run probability", lineup, result)

    with opt_col:
        if st.button("Optimize batting order", type="primary", use_container_width=True):
            with st.spinner("Testing candidate orders..."):
                optimized = optimize_lineup_order(
                    lineup,
                    games_per_order=optimize_games,
                    final_games=games,
                    random_order_count=random_orders,
                    seed=seed,
                    innings_per_game=9,
                    config=config,
                )
            _show_result(
                f"Optimized order ({optimized.label}, {optimized.orders_tested} orders tested)",
                optimized.lineup,
                optimized.result.runs_per_game,
                optimized.result.run_std,
                optimized.result.games,
            )


def _show_result(label: str, lineup: list[HitterProfile], runs: float, run_std: float, games: int) -> None:
    st.metric(label, f"{runs:.3f} runs / 9")
    st.caption(f"{games:,} simulations, run std {run_std:.3f}")
    st.code(lineup_names(lineup), language=None)


def _show_one_run_result(label: str, lineup: list[HitterProfile], result: object) -> None:
    st.metric(label, f"{result.probability:.3%}")
    st.caption(f"{result.trials:,} trials, 95% CI {result.ci95_low:.3%} to {result.ci95_high:.3%}")
    st.code(lineup_names(lineup), language=None)


def _lineup_entry(row: dict[str, object], source: str) -> dict[str, object]:
    return {
        "instance_id": str(uuid4()),
        "source": source,
        "row": row,
    }


def _player_label(row: pd.Series) -> str:
    return f"{row['player_name']} ({row.get('team', '')}, {int(row.get('season', 2025))}) - wOBA {row.get('woba', 0):.3f}"


def _entry_label(entry: dict[str, object]) -> str:
    row = entry["row"]
    source = "custom" if entry["source"] == "custom" else "season"
    return f"{row['player_name']} - {source} - wOBA {float(row.get('woba', 0)):.3f} - HR {int(row.get('hr', 0))}"


def _saved_custom_label(row: dict[str, object]) -> str:
    return (
        f"{row['player_name']} - wOBA {float(row.get('woba', 0)):.3f} - "
        f"{int(row.get('hr', 0))} HR - Sprint {float(row.get('sprint_speed', 27.0)):.1f} - "
        f"H2F {float(row.get('home_to_first', 4.35)):.2f} - {int(row.get('sb', 0))}/{int(row.get('cs', 0))} SB/CS - "
        f"{int(row.get('bb', 0))}/{int(row.get('k', 0))} BB/SO - "
        f"{row.get('eligible_groups', 'UTIL only')}"
    )


def _custom_hitter_row(**values: object) -> dict[str, object]:
    row = dict(values)
    plate_appearances = int(row["pa"])
    at_bats = int(row["ab"])
    walks = int(row["bb"])
    hbp = int(row["hbp"])
    row["player_id"] = f"custom-{uuid4()}"
    row["player_name"] = str(row.pop("name") or "Custom Hitter")
    source_player_id = str(row.pop("source_player_id", "") or "")
    source_mlbam_id = str(row.pop("source_mlbam_id", "") or "")
    if source_player_id:
        row["source_player_id"] = source_player_id
    if source_mlbam_id:
        row["mlbam_id"] = source_mlbam_id
        row["source_mlbam_id"] = source_mlbam_id
    row["season"] = 2025
    row["team"] = "CUSTOM"
    row["primary_position"] = "DH"
    row["ibb"] = int(row.get("ibb", 0))
    row["sf"] = int(row.get("sf", 0))
    row["sh"] = int(row.get("sh", 0))
    row["popup_rate"] = float(row.get("popup_rate", 0.05))
    source_woba = _number_or_default(row.pop("source_woba", 0.0), 0.0)
    source_wrc_plus = _number_or_default(row.pop("source_wrc_plus", 100.0), 100.0)
    source_events_match = _source_events_match(row)
    row["woba"] = source_woba if source_events_match and source_woba > 0 else _quick_woba(row)
    row["wrc_plus"] = source_wrc_plus if source_events_match else 100.0
    row["source_woba"] = source_woba
    row["source_wrc_plus"] = source_wrc_plus
    row["custom_woba_estimated"] = not source_events_match
    row["obp"] = _safe_divide(
        int(row["single"]) + int(row["double"]) + int(row["triple"]) + int(row["hr"]) + walks + hbp,
        plate_appearances,
    )
    row["slg"] = _safe_divide(
        int(row["single"]) + (2 * int(row["double"])) + (3 * int(row["triple"])) + (4 * int(row["hr"])),
        at_bats,
    )
    row["iso"] = row["slg"] - _safe_divide(
        int(row["single"]) + int(row["double"]) + int(row["triple"]) + int(row["hr"]),
        at_bats,
    )
    row["bb_rate"] = _safe_divide(walks, plate_appearances)
    row["k_rate"] = _safe_divide(int(row["k"]), plate_appearances)
    row["bsr"] = 0.0
    row["war"] = 0.0
    row["rdp"] = float(row["rdp"])
    row["sprint_speed"] = float(row["sprint_speed"])
    row["home_to_first"] = float(row["home_to_first"])
    row["gdp"] = 0
    row["gdp_per_pa"] = 0.0
    row["gdp_runs"] = float(row["rdp"])
    row["xbh"] = int(row["double"]) + int(row["triple"]) + int(row["hr"])
    row["xbh_per_ab"] = _safe_divide(row["xbh"], at_bats)
    row["hr_per_ab"] = _safe_divide(int(row["hr"]), at_bats)
    row["single_per_ab"] = _safe_divide(int(row["single"]), at_bats)
    row["bb_per_k"] = _safe_divide(walks, int(row["k"]))
    row["other_out"] = plate_appearances - walks - hbp - int(row["single"]) - int(row["double"]) - int(row["triple"]) - int(row["hr"]) - int(row["k"])
    for outcome in ("bb", "hbp", "single", "double", "triple", "hr", "k", "other_out"):
        row[f"p_{outcome}"] = _safe_divide(int(row[outcome]), plate_appearances)
    _add_custom_position_eligibility(row)
    return row




def _add_custom_position_eligibility(row: dict[str, object]) -> None:
    row["c"] = int(row.pop("c_games", 0))
    row["1b"] = int(row.pop("first_base_games", 0))
    row["2b"] = int(row.pop("second_base_games", 0))
    row["3b"] = int(row.pop("third_base_games", 0))
    row["ss"] = int(row.pop("shortstop_games", 0))
    row["of"] = int(row.pop("outfield_games", 0))
    row["eligible_c"] = row["c"] >= 20
    row["eligible_cif"] = row["1b"] >= 20 or row["3b"] >= 20
    row["eligible_mif"] = row["2b"] >= 20 or row["ss"] >= 20
    row["eligible_of"] = row["of"] >= 20
    row["eligible_util"] = True
    groups = []
    if row["eligible_c"]:
        groups.append("C")
    if row["eligible_cif"]:
        groups.append("1B/3B")
    if row["eligible_mif"]:
        groups.append("2B/SS")
    if row["eligible_of"]:
        groups.append("OF")
    row["eligible_groups"] = "; ".join(groups) if groups else "UTIL only"
    row["matched_bref_position_data"] = False
def _source_events_match(row: dict[str, object]) -> bool:
    source_fields = {
        "pa": row.pop("source_pa", 0),
        "ab": row.pop("source_ab", 0),
        "single": row.pop("source_single", 0),
        "double": row.pop("source_double", 0),
        "triple": row.pop("source_triple", 0),
        "hr": row.pop("source_hr", 0),
        "bb": row.pop("source_bb", 0),
        "hbp": row.pop("source_hbp", 0),
        "k": row.pop("source_k", 0),
    }
    if not source_fields["pa"]:
        return False
    return all(int(row.get(field, -1)) == int(value) for field, value in source_fields.items())

def _validate_custom_hitter(row: dict[str, object]) -> str | None:
    if int(row["other_out"]) < 0:
        return "The entered events exceed PA. Lower the event totals or raise PA."
    probability_sum = sum(float(row[f"p_{outcome}"]) for outcome in ("bb", "hbp", "single", "double", "triple", "hr", "k", "other_out"))
    if abs(probability_sum - 1.0) > 0.000001:
        return "Custom hitter probabilities do not sum to 1. Check the inputs."
    return None


def _quick_woba(row: dict[str, object]) -> float:
    numerator = (
        0.69 * int(row["bb"])
        + 0.72 * int(row["hbp"])
        + 0.88 * int(row["single"])
        + 1.25 * int(row["double"])
        + 1.58 * int(row["triple"])
        + 2.0 * int(row["hr"])
    )
    return _safe_divide(numerator, int(row["pa"]))


def _number_or_default(value: object, default: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if pd.isna(numeric):
        return float(default)
    return numeric


def _int_or_default(value: object, default: int) -> int:
    return int(round(_number_or_default(value, float(default))))

def _safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


if __name__ == "__main__":
    main()








