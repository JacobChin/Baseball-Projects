import math
from pathlib import Path

import numpy as np
import pandas as pd

from baseball_lineup_optimizer.engine.evaluator import DEFAULT_STOLEN_BASE_RATES_PATH, attach_stolen_base_rates
from baseball_lineup_optimizer.engine.outcomes import HitterProfile, make_synthetic_hitter
from baseball_lineup_optimizer.engine.plan_engine import (
    PlanEngineConfig,
    RunnerBaseState,
    _steal_attempt_rate,
    _steal_success_rate,
    apply_pre_pa_steal,
)


def _profile(metadata):
    hitter = make_synthetic_hitter(
        "Runner",
        {"bb": 0.1, "hbp": 0.0, "single": 0.1, "double": 0.05, "triple": 0.0, "hr": 0.05, "k": 0.2, "other_out": 0.5},
    )
    return HitterProfile(hitter.player_id, hitter.player_name, hitter.probabilities, metadata)


def test_revised_stolen_base_rates_override_raw_sb_cs_by_target():
    runner = _profile(
        {
            "pa": 600,
            "sb": 0,
            "cs": 0,
            "steal_2b_attempt_probability": 0.12,
            "steal_2b_success_probability": 0.81,
            "steal_3b_attempt_probability": 0.03,
            "steal_3b_success_probability": 0.74,
        }
    )
    config = PlanEngineConfig(steal_attempt_multiplier=0.5, steal_third_attempt_multiplier=0.0)

    assert math.isclose(_steal_attempt_rate(runner, config, "second"), 0.06)
    assert math.isclose(_steal_success_rate(runner, config, "second"), 0.81)
    assert math.isclose(_steal_attempt_rate(runner, config, "third"), 0.015)
    assert math.isclose(_steal_success_rate(runner, config, "third"), 0.74)


def test_raw_sb_cs_fallback_still_applies_to_custom_players():
    runner = _profile({"pa": 100, "sb": 10, "cs": 0})
    config = PlanEngineConfig()

    expected_second_attempt = ((0.10 * 100) + (config.steal_attempt_prior_rate * config.steal_attempt_prior_pa)) / 200
    assert math.isclose(_steal_attempt_rate(runner, config, "second"), expected_second_attempt)
    assert math.isclose(_steal_attempt_rate(runner, config, "third"), expected_second_attempt * config.steal_third_attempt_multiplier)

    expected_third_success = (10 + config.default_steal_success_rate * config.steal_third_success_prior_attempts) / (10 + config.steal_third_success_prior_attempts)
    assert math.isclose(_steal_success_rate(runner, config, "third"), expected_third_success)


def test_attach_stolen_base_rates_merges_by_mlbam_id(tmp_path):
    rates = pd.DataFrame(
        [
            {"runner_id": 123, "target_base": "2B", "standardized_attempt_probability_per_pa": 0.11, "standardized_success_probability": 0.80},
            {"runner_id": 123, "target_base": "3B", "standardized_attempt_probability_per_pa": 0.02, "standardized_success_probability": 0.76},
        ]
    )
    rates_path = tmp_path / "rates.csv"
    rates.to_csv(rates_path, index=False)
    pool = pd.DataFrame([{"mlbam_id": 123, "player_name": "Runner"}, {"mlbam_id": 999, "player_name": "Other"}])

    enriched = attach_stolen_base_rates(pool, rates_path)

    row = enriched[enriched["mlbam_id"].eq(123)].iloc[0]
    assert math.isclose(row["steal_2b_attempt_probability"], 0.11)
    assert math.isclose(row["steal_2b_success_probability"], 0.80)
    assert math.isclose(row["steal_3b_attempt_probability"], 0.02)
    assert math.isclose(row["steal_3b_success_probability"], 0.76)
    other = enriched[enriched["mlbam_id"].eq(999)].iloc[0]
    assert pd.isna(other["steal_2b_attempt_probability"])



def test_contextual_stolen_base_rates_vary_by_base_out_state_and_override_legacy():
    runner = _profile(
        {
            "steal_2b_attempt_1xx_0": 0.10,
            "steal_2b_attempt_1xx_1": 0.20,
            "steal_2b_attempt_1x3_0": 0.30,
            "steal_2b_success_1xx": 0.70,
            "steal_2b_success_1x3": 0.90,
            "steal_2b_attempt_probability": 0.99,
            "steal_2b_success_probability": 0.50,
        }
    )
    config = PlanEngineConfig(max_steal_attempt_rate=1.0)

    assert math.isclose(_steal_attempt_rate(runner, config, "second", base_state="1--", outs=0), 0.10)
    assert math.isclose(_steal_attempt_rate(runner, config, "second", base_state="1--", outs=1), 0.20)
    assert math.isclose(_steal_attempt_rate(runner, config, "second", base_state="1-3", outs=0), 0.30)
    assert math.isclose(_steal_success_rate(runner, config, "second", base_state="1--", outs=0), 0.70)
    assert math.isclose(_steal_success_rate(runner, config, "second", base_state="1-3", outs=2), 0.90)


def test_steal_third_only_allowed_from_second_base_empty_corners():
    runner = _profile({"steal_3b_attempt_x2x_0": 1.0, "steal_3b_success_x2x": 1.0})
    blocker = _profile({})
    config = PlanEngineConfig(max_steal_attempt_rate=1.0)

    blocked = apply_pre_pa_steal(RunnerBaseState(first=blocker, second=runner, outs=0), np.random.default_rng(1), config)
    assert blocked.state.first == blocker
    assert blocked.state.second == runner
    assert blocked.state.third is None

    allowed = apply_pre_pa_steal(RunnerBaseState(second=runner, outs=0), np.random.default_rng(1), config)
    assert allowed.state.first is None
    assert allowed.state.second is None
    assert allowed.state.third == runner


def test_contextual_steal_second_from_first_and_third_is_single_action():
    runner = _profile({"steal_2b_attempt_1x3_0": 1.0, "steal_2b_success_1x3": 1.0})
    third_runner = _profile({})
    config = PlanEngineConfig(max_steal_attempt_rate=1.0)

    result = apply_pre_pa_steal(RunnerBaseState(first=runner, third=third_runner, outs=0), np.random.default_rng(2), config)

    assert result.state.first is None
    assert result.state.second == runner
    assert result.state.third == third_runner
    assert result.runs == 0
    assert result.plate_appearance_completed is True


def test_contextual_caught_stealing_can_end_inning_without_completing_pa():
    runner = _profile({"steal_2b_attempt_1xx_2": 1.0, "steal_2b_success_1xx": 0.0})
    config = PlanEngineConfig(max_steal_attempt_rate=1.0)

    result = apply_pre_pa_steal(RunnerBaseState(first=runner, outs=2), np.random.default_rng(3), config)

    assert result.state.outs == 3
    assert result.state.first is None
    assert result.plate_appearance_completed is False


def test_attach_contextual_stolen_base_rates_merges_wide_runtime_columns(tmp_path):
    rates = pd.DataFrame(
        [
            {
                "runner_id": 123,
                "steal_2b_attempt_1xx_0": 0.11,
                "steal_2b_success_1xx": 0.80,
                "steal_3b_attempt_x2x_1": 0.03,
                "steal_3b_success_x2x": 0.76,
                "stolen_base_context": '{"2B": {}}',
            }
        ]
    )
    rates_path = tmp_path / "contextual_rates.csv"
    rates.to_csv(rates_path, index=False)
    pool = pd.DataFrame([{"mlbam_id": 123, "player_name": "Runner"}, {"mlbam_id": 999, "player_name": "Other"}])

    enriched = attach_stolen_base_rates(pool, rates_path)

    row = enriched[enriched["mlbam_id"].eq(123)].iloc[0]
    assert math.isclose(row["steal_2b_attempt_1xx_0"], 0.11)
    assert math.isclose(row["steal_2b_success_1xx"], 0.80)
    assert math.isclose(row["steal_3b_attempt_x2x_1"], 0.03)
    assert row["stolen_base_context"] == '{"2B": {}}'



def test_default_stolen_base_artifact_is_promoted_beta_binomial():
    root = Path(__file__).resolve().parents[1]
    production = pd.read_csv(root / DEFAULT_STOLEN_BASE_RATES_PATH)
    beta = pd.read_csv(root / "data/processed/contextual_stolen_base_rates_2025_behavioral_shrinkage_revised.csv")

    pd.testing.assert_frame_equal(production, beta)
    assert (root / "data/processed/contextual_stolen_base_rates_2025_legacy_complex.csv").exists()


def test_missing_player_contextual_fallback_uses_behavioral_league_defaults():
    runner = _profile({})
    config = PlanEngineConfig(max_steal_attempt_rate=1.0)

    assert math.isclose(_steal_attempt_rate(runner, config, "second", base_state="1--", outs=0), 0.075396)
    assert math.isclose(_steal_attempt_rate(runner, config, "second", base_state="1-3", outs=2), 0.101454)
    assert math.isclose(_steal_attempt_rate(runner, config, "third", base_state="-2-", outs=1), 0.022160)
    assert math.isclose(_steal_success_rate(runner, config, "second", base_state="1--", outs=0), 0.746588)
    assert math.isclose(_steal_success_rate(runner, config, "second", base_state="1-3", outs=2), 0.915400)
    assert math.isclose(_steal_success_rate(runner, config, "third", base_state="-2-", outs=1), 0.785033)
