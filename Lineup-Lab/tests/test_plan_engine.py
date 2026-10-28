import numpy as np

from baseball_lineup_optimizer.engine.outcomes import HitterProfile, make_synthetic_hitter
from baseball_lineup_optimizer.engine.plan_engine import (
    PlanEngineConfig,
    RunnerBaseState,
    _double_play_multiplier,
    _fitted_gdp_home_to_first_multiplier,
    apply_plan_plate_appearance,
    expected_runs_plan,
    plan_probabilities,
)


def test_plan_probabilities_remove_ibb_and_sh_from_sample():
    hitter = HitterProfile(
        player_id="1",
        player_name="Selective Hitter",
        probabilities={
            "bb": 0.20,
            "hbp": 0.01,
            "single": 0.10,
            "double": 0.05,
            "triple": 0.00,
            "hr": 0.05,
            "k": 0.20,
            "other_out": 0.39,
        },
        metadata={
            "pa": 100,
            "bb": 20,
            "ibb": 5,
            "sh": 3,
            "hbp": 1,
            "single": 10,
            "double": 5,
            "triple": 0,
            "hr": 5,
            "k": 20,
            "gb_rate": 0.4,
            "fb_rate": 0.3,
            "ld_rate": 0.2,
            "popup_rate": 0.1,
        },
    )

    probs = plan_probabilities(hitter)

    assert probs["bb"] == 15 / 92
    assert abs(sum(probs.values()) - 1.0) < 1e-12
    assert probs["popup_out"] > 0
    assert probs["gb_out"] > probs["popup_out"]


def test_walk_forces_only_required_runners_plan_engine():
    batter = _hitter("Batter")
    runner = _hitter("Runner")
    state = RunnerBaseState(first=runner, third=runner, outs=1)

    result = apply_plan_plate_appearance(state, batter, "bb", np.random.default_rng(1))

    assert result.runs == 0
    assert result.state.first == batter
    assert result.state.second == runner
    assert result.state.third == runner
    assert result.state.outs == 1


def test_popup_out_holds_all_runners():
    batter = _hitter("Batter")
    runner = _hitter("Runner")
    state = RunnerBaseState(first=runner, second=runner, third=runner, outs=0)

    result = apply_plan_plate_appearance(state, batter, "popup_out", np.random.default_rng(1))

    assert result.runs == 0
    assert result.state.first == runner
    assert result.state.second == runner
    assert result.state.third == runner
    assert result.state.outs == 1


def test_lineout_can_hold_runners_with_zero_doubleoff_rate():
    batter = _hitter("Batter")
    runner = _hitter("Runner")
    config = PlanEngineConfig(lineout_doubleoff_rate=0.0)
    state = RunnerBaseState(first=runner, outs=1)

    result = apply_plan_plate_appearance(state, batter, "ld_out", np.random.default_rng(1), config)

    assert result.runs == 0
    assert result.state.first == runner
    assert result.state.outs == 2


def test_plan_engine_simulates_nine_hitter_lineup():
    lineup = [_hitter(f"Hitter {i}") for i in range(9)]

    result = expected_runs_plan(lineup, games=50, seed=7)

    assert result.games == 50
    assert result.innings_per_game == 9
    assert result.runs_per_game >= 0


def test_empirical_speed_attempt_mode_is_default_and_falls_back_neutral(tmp_path):
    lineup = [_hitter(f"Hitter {i}") for i in range(9)]
    config = PlanEngineConfig(
        use_empirical_transitions=True,
        runner_advancement_model="empirical_speed_attempt",
        speed_attempt_model_path=str(tmp_path / "missing_speed_attempt_model.json"),
    )

    result = expected_runs_plan(lineup, games=5, seed=11, config=config)

    assert PlanEngineConfig().runner_advancement_model == "empirical_speed_attempt"
    assert result.games == 5
    assert result.runs_per_game >= 0


def test_fitted_gdp_home_to_first_multiplier_matches_audit_grid():
    assert _fitted_gdp_home_to_first_multiplier(4.35) == 1.0
    assert np.isclose(_fitted_gdp_home_to_first_multiplier(4.05), 0.657371, atol=1e-6)
    assert np.isclose(_fitted_gdp_home_to_first_multiplier(4.55), 1.280019, atol=1e-6)
    assert np.isclose(_fitted_gdp_home_to_first_multiplier(4.90), 1.829132, atol=1e-6)


def test_double_play_multiplier_prefers_fitted_home_to_first_over_old_inputs():
    fast = _hitter("Fast")
    fast.metadata.update({"home_to_first": 4.05, "sprint_speed": 24.0, "rdp": -5.0, "pa": 600})
    neutral = _hitter("Neutral")
    neutral.metadata.update({"home_to_first": 4.35})
    slow = _hitter("Slow")
    slow.metadata.update({"home_to_first": 4.90})

    assert _double_play_multiplier(fast, PlanEngineConfig()) < _double_play_multiplier(neutral, PlanEngineConfig())
    assert _double_play_multiplier(slow, PlanEngineConfig()) > _double_play_multiplier(neutral, PlanEngineConfig())
    assert np.isclose(_double_play_multiplier(fast, PlanEngineConfig()), _fitted_gdp_home_to_first_multiplier(4.05), atol=1e-12)

def _hitter(name: str):
    return make_synthetic_hitter(
        name,
        {"bb": 0.1, "hbp": 0.0, "single": 0.1, "double": 0.05, "triple": 0.0, "hr": 0.05, "k": 0.2, "other_out": 0.5},
    )



def test_multiyear_bip_artifacts_are_default():
    from baseball_lineup_optimizer.engine.speed_attempt_models import DEFAULT_SPEED_ATTEMPT_MODEL_PATH
    from baseball_lineup_optimizer.engine.transition_models import DEFAULT_TRANSITION_MODEL_PATH

    assert DEFAULT_TRANSITION_MODEL_PATH.name == "transition_models_2021_2025_direct_movement.json"
    assert DEFAULT_SPEED_ATTEMPT_MODEL_PATH.name == "speed_attempt_models_2021_2025_direct_movement.json"


def test_transition_model_preserves_compact_counts(tmp_path):
    import json

    from baseball_lineup_optimizer.engine.transition_models import TransitionModel

    path = tmp_path / "transition.json"
    path.write_text(
        json.dumps(
            {
                "season": 2025,
                "min_exact_count": 1,
                "transitions": {
                    "single|0|1--|rf": [
                        {"batter": "first", "first": "third", "second": "empty", "third": "empty", "outs_added": 0, "runs": 0, "count": 7}
                    ]
                },
                "hitter_distributions": {},
                "league_distributions": {},
            }
        ),
        encoding="utf-8",
    )

    model = TransitionModel.from_json(path)

    assert model.model_summary()["transition_rows"] == 7
    assert model.transitions["single|0|1--|rf"][0]["count"] == 7
