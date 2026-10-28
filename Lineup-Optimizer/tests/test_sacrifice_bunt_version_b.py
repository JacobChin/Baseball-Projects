
import math

import numpy as np

from baseball_lineup_optimizer.engine.outcomes import make_synthetic_hitter
from baseball_lineup_optimizer.engine.plan_engine import PlanEngineConfig, PlayResult, RunnerBaseState
from baseball_lineup_optimizer.engine.sacrifice_bunt import (
    BuntModel,
    ELIGIBLE_BUNT_STATES,
    is_eligible_bunt_state,
    simulate_policy_one_run,
    solve_one_run_mdp,
    state_key,
)
import baseball_lineup_optimizer.engine.sacrifice_bunt as sacrifice_bunt


def test_bunt_eligibility_exact_six_states():
    assert set(ELIGIBLE_BUNT_STATES) == {("1--", 0), ("1--", 1), ("-2-", 0), ("-2-", 1), ("12-", 0), ("12-", 1)}
    assert is_eligible_bunt_state(("1--", 0))
    assert not is_eligible_bunt_state(("---", 0))
    assert not is_eligible_bunt_state(("1-3", 0))
    assert not is_eligible_bunt_state(("1--", 2))


def test_optional_bunt_cannot_reduce_mdp_value():
    hitter = make_synthetic_hitter(
        "Test Hitter",
        {"bb": 0.08, "hbp": 0.01, "single": 0.16, "double": 0.05, "triple": 0.0, "hr": 0.04, "k": 0.20, "other_out": 0.46},
    )
    model = BuntModel(
        definition="test",
        rows=None,
        terminal_distributions={
            ("1--", 0): [{"next_base_state": "-2-", "next_outs": 1, "runs": 0, "reconciled_category": "credited_sacrifice", "count": 9}],
            ("1--", 1): [{"next_base_state": "-2-", "next_outs": 2, "runs": 0, "reconciled_category": "credited_sacrifice", "count": 9}],
            ("-2-", 0): [{"next_base_state": "--3", "next_outs": 1, "runs": 0, "reconciled_category": "credited_sacrifice", "count": 9}],
            ("-2-", 1): [{"next_base_state": "--3", "next_outs": 2, "runs": 0, "reconciled_category": "credited_sacrifice", "count": 9}],
            ("12-", 0): [{"next_base_state": "-23", "next_outs": 1, "runs": 0, "reconciled_category": "credited_sacrifice", "count": 9}],
            ("12-", 1): [{"next_base_state": "-23", "next_outs": 2, "runs": 0, "reconciled_category": "credited_sacrifice", "count": 9}],
        },
        global_terminal_distribution=[{"next_base_state": "---", "next_outs": 3, "runs": 0, "reconciled_category": "bunt_out_no_official_sac", "count": 1}],
        branch_rates={key: 0.0 for key in ELIGIBLE_BUNT_STATES},
        global_abandon_rate=0.0,
        player_effects={},
        league_success_rate=0.9,
        shrinkage_prior_strength=10.0,
    )
    config = PlanEngineConfig(use_empirical_transitions=False, use_contextual_walks=False, steal_attempt_multiplier=0.0)
    no_bunt = solve_one_run_mdp(hitter, config, None, samples_per_state=60, seed=1, disable_bunts=True)
    with_bunt = solve_one_run_mdp(hitter, config, model, samples_per_state=60, seed=1, disable_bunts=False)
    assert with_bunt.optimized_probability + 1e-12 >= no_bunt.optimized_probability
    assert all(math.isfinite(row["q_normal"]) for row in with_bunt.decision_rows)



def _minimal_bunt_model() -> BuntModel:
    return BuntModel(
        definition="test",
        rows=None,
        terminal_distributions={key: [{"next_base_state": "---", "next_outs": 3, "runs": 1, "reconciled_category": "credited_sacrifice", "count": 1}] for key in ELIGIBLE_BUNT_STATES},
        global_terminal_distribution=[{"next_base_state": "---", "next_outs": 3, "runs": 1, "reconciled_category": "credited_sacrifice", "count": 1}],
        branch_rates={key: 0.0 for key in ELIGIBLE_BUNT_STATES},
        global_abandon_rate=0.0,
        player_effects={},
        league_success_rate=1.0,
        shrinkage_prior_strength=1.0,
    )


def test_version_b_uses_post_steal_state_for_bunt_eligibility(monkeypatch):
    hitter = make_synthetic_hitter(
        "Runner",
        {"bb": 0.0, "hbp": 0.0, "single": 1.0, "double": 0.0, "triple": 0.0, "hr": 0.0, "k": 0.0, "other_out": 0.0},
    )
    calls = {"bunt_states": [], "pa": 0, "steals": 0}

    def fake_steal(state, rng, config):
        calls["steals"] += 1
        if state.first is not None and state.second is None and state.outs == 0:
            return PlayResult(RunnerBaseState(second=state.first, outs=0), plate_appearance_completed=True)
        return PlayResult(state, plate_appearance_completed=True)

    def fake_sample(*args, **kwargs):
        return "single"

    def fake_apply(state, batter, outcome, rng, config):
        calls["pa"] += 1
        assert state_key(state) == ("---", 0)
        return PlayResult(RunnerBaseState(first=batter, outs=0), runs=0)

    def fake_bunt(state, batter, model, rng, config):
        calls["bunt_states"].append(state_key(state))
        return PlayResult(RunnerBaseState(outs=state.outs), runs=1)

    monkeypatch.setattr(sacrifice_bunt, "apply_pre_pa_steal", fake_steal)
    monkeypatch.setattr(sacrifice_bunt, "sample_plan_outcome", fake_sample)
    monkeypatch.setattr(sacrifice_bunt, "apply_plan_plate_appearance", fake_apply)
    monkeypatch.setattr(sacrifice_bunt, "sample_bunt_plate_appearance", fake_bunt)

    policy = {key: "normal_pa" for key in ELIGIBLE_BUNT_STATES}
    policy[("-2-", 0)] = "sacrifice_bunt_strategy"
    result = simulate_policy_one_run(hitter, PlanEngineConfig(steal_attempt_multiplier=0.0), _minimal_bunt_model(), policy, trials=1, seed=1)

    assert result.successes == 1
    assert calls["bunt_states"] == [("-2-", 0)]
    assert calls["pa"] == 1
    assert calls["steals"] == 2


def test_version_b_caught_stealing_third_out_stops_before_pa(monkeypatch):
    hitter = make_synthetic_hitter(
        "Runner",
        {"bb": 0.0, "hbp": 0.0, "single": 1.0, "double": 0.0, "triple": 0.0, "hr": 0.0, "k": 0.0, "other_out": 0.0},
    )
    calls = {"pa": 0, "bunt": 0}

    def fake_steal(state, rng, config):
        if state.first is not None and state.outs == 2:
            return PlayResult(RunnerBaseState(outs=3), runs=0, plate_appearance_completed=False)
        return PlayResult(state, plate_appearance_completed=True)

    def fake_sample(*args, **kwargs):
        return "scripted"

    def fake_apply(state, batter, outcome, rng, config):
        calls["pa"] += 1
        if calls["pa"] == 1:
            return PlayResult(RunnerBaseState(first=batter, outs=0), runs=0)
        return PlayResult(RunnerBaseState(first=state.first, outs=state.outs + 1), runs=0)

    def fake_bunt(*args, **kwargs):
        calls["bunt"] += 1
        return PlayResult(RunnerBaseState(outs=3), runs=0)

    monkeypatch.setattr(sacrifice_bunt, "apply_pre_pa_steal", fake_steal)
    monkeypatch.setattr(sacrifice_bunt, "sample_plan_outcome", fake_sample)
    monkeypatch.setattr(sacrifice_bunt, "apply_plan_plate_appearance", fake_apply)
    monkeypatch.setattr(sacrifice_bunt, "sample_bunt_plate_appearance", fake_bunt)

    policy = {key: "normal_pa" for key in ELIGIBLE_BUNT_STATES}
    result = simulate_policy_one_run(hitter, PlanEngineConfig(steal_attempt_multiplier=0.0), _minimal_bunt_model(), policy, trials=1, seed=1)

    assert result.successes == 0
    assert calls["pa"] == 3
    assert calls["bunt"] == 0
