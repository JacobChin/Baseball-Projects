
import math

import numpy as np

from baseball_lineup_optimizer.engine.outcomes import make_synthetic_hitter
from baseball_lineup_optimizer.engine.plan_engine import (
    PlanEngineConfig,
    _risp_initial_state,
    expected_one_run_probability_plan,
    expected_risp_one_run_probability_plan,
    expected_runs_plan,
    simulate_one_run_trial,
)


def hitter(name, **probabilities):
    return make_synthetic_hitter(name, probabilities)


def test_one_run_trial_starts_empty_and_stops_immediately_on_first_run():
    slugger = hitter("Slugger", hr=1.0)

    result = simulate_one_run_trial([slugger] * 9, np.random.default_rng(1), config=PlanEngineConfig())

    assert result.success is True
    assert result.plate_appearances == 1
    assert result.first_run_outs == 0
    assert result.batting_slots_completed == (1,)
    assert result.final_outs == 0


def test_one_run_trial_fails_at_third_out_without_second_inning():
    strikeout = hitter("Out", k=1.0)

    result = simulate_one_run_trial([strikeout] * 9, np.random.default_rng(2), config=PlanEngineConfig())

    assert result.success is False
    assert result.plate_appearances == 3
    assert result.final_outs == 3
    assert result.batting_slots_completed == (1, 2, 3)


def test_one_run_probability_summary_reports_zero_run_probability_and_ci():
    slugger = hitter("Slugger", hr=1.0)

    result = expected_one_run_probability_plan([slugger] * 9, trials=25, seed=3, config=PlanEngineConfig())

    assert result.successes == 25
    assert result.failures == 0
    assert result.probability == 1.0
    assert result.standard_error == 0.0
    assert result.first_run_out_0_probability == 1.0


def test_clone_contextual_walk_call_uses_late_tie_and_same_batter_ondeck(monkeypatch):
    calls = []

    class FakeWalkModel:
        def predict_probability(self, batter_id, ondeck_id, base_state, outs, inning, score_diff=None):
            calls.append(
                {
                    "batter_id": batter_id,
                    "ondeck_id": ondeck_id,
                    "base_state": base_state,
                    "outs": outs,
                    "inning": inning,
                    "score_diff": score_diff,
                }
            )
            return 0.0

    import baseball_lineup_optimizer.engine.plan_engine as plan_engine

    monkeypatch.setattr(plan_engine, "load_contextual_walk_model", lambda _path: FakeWalkModel())
    out = hitter("Clone", k=1.0)
    out = type(out)(out.player_id, out.player_name, out.probabilities, {"mlbam_id": 123})
    config = PlanEngineConfig(use_contextual_walks=True)

    simulate_one_run_trial([out] * 9, np.random.default_rng(4), config=config)

    assert calls
    assert all(call["batter_id"] == 123 and call["ondeck_id"] == 123 for call in calls)
    assert all(call["inning"] == 7 for call in calls)
    assert all(call["score_diff"] == 0.0 for call in calls)


def test_normal_runs_per_9_path_still_works_after_adding_one_run_mode():
    out = hitter("Out", k=1.0)

    result = expected_runs_plan([out] * 9, games=5, seed=5, innings_per_game=9, config=PlanEngineConfig())

    assert math.isclose(result.runs_per_game, 0.0)
    assert result.games == 5

def test_risp_probability_scores_for_certain_home_run_and_not_for_certain_strikeout():
    slugger = hitter("Slugger", hr=1.0)
    strikeout = hitter("Out", k=1.0)

    slugger_result = expected_risp_one_run_probability_plan(
        [slugger] * 9,
        trials=180,
        seed=6,
        config=PlanEngineConfig(),
    )
    strikeout_result = expected_risp_one_run_probability_plan(
        [strikeout] * 9,
        trials=180,
        seed=6,
        config=PlanEngineConfig(),
    )

    assert slugger_result.probability == 1.0
    assert strikeout_result.probability == 0.0
    assert slugger_result.trials == 180


def test_risp_initial_state_uses_preceding_lineup_slots_for_existing_runners():
    lineup = [hitter(f"Hitter {index}", k=1.0) for index in range(1, 10)]

    state = _risp_initial_state(lineup, "123", outs=1)

    assert state.first is lineup[8]
    assert state.second is lineup[7]
    assert state.third is lineup[6]
    assert state.outs == 1
