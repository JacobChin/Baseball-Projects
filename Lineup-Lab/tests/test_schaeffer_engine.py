import numpy as np

from baseball_lineup_optimizer.engine.outcomes import HitterProfile, make_synthetic_hitter
from baseball_lineup_optimizer.engine.schaeffer import (
    BaserunningConfig,
    ExtraBaseProbabilities,
    RunnerBaseState,
    apply_plate_appearance,
    double_play_rate,
    schaeffer_probabilities,
)


def test_schaeffer_probabilities_split_other_outs_by_batted_ball_profile():
    hitter = HitterProfile(
        player_id="1",
        player_name="Groundball Hitter",
        probabilities={
            "bb": 0.1,
            "hbp": 0.0,
            "single": 0.1,
            "double": 0.05,
            "triple": 0.0,
            "hr": 0.05,
            "k": 0.2,
            "other_out": 0.5,
        },
        metadata={"gb_rate": 0.50, "fb_rate": 0.30, "ld_rate": 0.20},
    )

    probabilities = schaeffer_probabilities(hitter)

    assert probabilities["groundout"] == 0.25
    assert probabilities["airout"] == 0.25
    assert sum(probabilities.values()) == 1.0


def test_walk_forces_only_when_required():
    batter = _hitter("Batter")
    runner = _hitter("Runner")
    state = RunnerBaseState(first=runner, third=runner, outs=1)

    result = apply_plate_appearance(state, batter, "bb", np.random.default_rng(1))

    assert result.runs == 0
    assert result.state.first == batter
    assert result.state.second == runner
    assert result.state.third == runner
    assert result.state.outs == 1


def test_triple_scores_all_existing_runners():
    batter = _hitter("Batter")
    runner = _hitter("Runner")
    state = RunnerBaseState(first=runner, second=runner, third=runner, outs=1)

    result = apply_plate_appearance(state, batter, "triple", np.random.default_rng(1))

    assert result.runs == 3
    assert result.state.first is None
    assert result.state.second is None
    assert result.state.third == batter
    assert result.state.outs == 1


def test_single_can_score_runner_from_second_with_configured_success():
    batter = _hitter("Batter")
    first_runner = _hitter("First")
    second_runner = _hitter("Second")
    config = BaserunningConfig(
        second_to_home_on_single=ExtraBaseProbabilities(0.0, 1.0, 0.0),
        first_to_third_on_single=ExtraBaseProbabilities(0.0, 1.0, 0.0),
    )
    state = RunnerBaseState(first=first_runner, second=second_runner, outs=0)

    result = apply_plate_appearance(state, batter, "single", np.random.default_rng(1), config)

    assert result.runs == 1
    assert result.state.first == batter
    assert result.state.second is None
    assert result.state.third == first_runner


def test_xbt_rate_scales_hit_based_extra_base_success():
    batter = _hitter("Batter")
    fast_runner = _hitter_with_metadata("Fast Runner", {"xbt_rate": 0.70})
    slow_runner = _hitter_with_metadata("Slow Runner", {"xbt_rate": 0.20})
    config = BaserunningConfig(
        first_to_third_on_single=ExtraBaseProbabilities(0.5, 0.5, 0.0),
        league_xbt_rate=0.40,
    )

    fast_successes = 0
    slow_successes = 0
    for seed in range(200):
        fast = apply_plate_appearance(RunnerBaseState(first=fast_runner), batter, "single", np.random.default_rng(seed), config)
        slow = apply_plate_appearance(RunnerBaseState(first=slow_runner), batter, "single", np.random.default_rng(seed), config)
        fast_successes += int(fast.state.third == fast_runner)
        slow_successes += int(slow.state.third == slow_runner)

    assert fast_successes > slow_successes


def test_double_play_rate_uses_gdp_runs_directionally():
    good_avoider = _hitter_with_metadata("DP Avoider", {"pa": 600, "gdp_runs": 2.0})
    bad_avoider = _hitter_with_metadata("DP Prone", {"pa": 600, "gdp_runs": -2.0})

    assert double_play_rate(good_avoider) < 0.11
    assert double_play_rate(bad_avoider) > 0.11


def test_double_play_rate_prefers_rdp_over_gdp_runs():
    hitter = _hitter_with_metadata("Rdp Hitter", {"pa": 600, "rdp": 2.0, "gdp_runs": -2.0})

    assert double_play_rate(hitter) < 0.11


def test_double_play_rate_falls_back_to_raw_gdp_per_pa():
    hitter = _hitter_with_metadata("Raw GDP Hitter", {"pa": 600, "gdp": 24})

    assert double_play_rate(hitter) > 0.11


def test_double_play_rate_fallback_rewards_zero_gdp():
    hitter = _hitter_with_metadata("Zero GDP Hitter", {"pa": 600, "gdp": 0})

    assert double_play_rate(hitter) < 0.11


def _hitter(name: str):
    return make_synthetic_hitter(
        name,
        {"bb": 0.1, "hbp": 0.0, "single": 0.1, "double": 0.05, "triple": 0.0, "hr": 0.05, "k": 0.2, "other_out": 0.5},
    )


def _hitter_with_metadata(name: str, metadata: dict[str, float]) -> HitterProfile:
    hitter = _hitter(name)
    return HitterProfile(
        player_id=hitter.player_id,
        player_name=hitter.player_name,
        probabilities=hitter.probabilities,
        metadata=metadata,
    )
