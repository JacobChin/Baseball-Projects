"""Plan-aligned Monte Carlo offense engine.

This engine implements the first working version of the user's 2025 MLB offense
simulation plan. It keeps the simulation PA-level, removes IBBs and sacrifice
bunts from player event probabilities when those counts are available, separates
outs into GB/FB/LD/popup, excludes WP/PB/errors, and simulates normal 9-inning
offensive games.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Mapping, Sequence

import numpy as np

from baseball_lineup_optimizer.engine.contextual_walks import (
    DEFAULT_CONTEXTUAL_WALK_MODEL_PATH,
    load_contextual_walk_model,
)
from baseball_lineup_optimizer.engine.outcomes import HitterProfile
from baseball_lineup_optimizer.engine.speed_attempt_models import (
    DEFAULT_SPEED_ATTEMPT_MODEL_PATH,
    NEUTRAL_SPRINT_SPEED,
    SpeedAttemptStats,
    load_speed_attempt_model,
)
from baseball_lineup_optimizer.engine.simulation import SimulationResult
from baseball_lineup_optimizer.engine.transition_models import (
    DEFAULT_TRANSITION_MODEL_PATH,
    EmpiricalTransition,
    TransitionModel,
    base_state_from_occupancy,
    load_transition_model,
)


PLAN_OUTCOMES = (
    "bb",
    "hbp",
    "single",
    "double",
    "triple",
    "hr",
    "k",
    "gb_out",
    "fb_out",
    "ld_out",
    "popup_out",
)


FITTED_GDP_HT1_INTERCEPT = -0.707111
FITTED_GDP_HT1_COEFFICIENT = 0.361611
FITTED_GDP_HT1_MEAN = 4.469196426292279
FITTED_GDP_HT1_SCALE = 0.1983359943369858
FITTED_GDP_NEUTRAL_HOME_TO_FIRST = 4.35
FITTED_GDP_MIN_HOME_TO_FIRST = 3.97
FITTED_GDP_MAX_HOME_TO_FIRST = 5.26
FITTED_GDP_MIN_MULTIPLIER = 0.50
FITTED_GDP_MAX_MULTIPLIER = 2.50


@dataclass(frozen=True)
class CategoricalProbabilities:
    """No-attempt/hold, safe advance, and out-advancing probabilities."""

    hold: float
    advance: float
    out: float


@dataclass(frozen=True)
class PlanEngineConfig:
    """Version-1 plan-engine assumptions.

    These constants are deliberately transparent placeholders until the full 2025
    joint transition models are fit from Statcast play outcomes.
    """

    first_to_third_on_single: CategoricalProbabilities = CategoricalProbabilities(0.638, 0.349, 0.013)
    second_to_home_on_single: CategoricalProbabilities = CategoricalProbabilities(0.352, 0.617, 0.031)
    first_to_home_on_double: CategoricalProbabilities = CategoricalProbabilities(0.635, 0.338, 0.027)
    second_to_third_on_groundout: CategoricalProbabilities = CategoricalProbabilities(0.315, 0.644, 0.041)
    third_to_home_on_groundout: CategoricalProbabilities = CategoricalProbabilities(0.138, 0.552, 0.310)
    second_to_third_on_flyout: CategoricalProbabilities = CategoricalProbabilities(0.766, 0.221, 0.013)
    third_to_home_on_flyout: CategoricalProbabilities = CategoricalProbabilities(0.391, 0.524, 0.085)
    groundout_double_play_rate: float = 0.11
    lineout_doubleoff_rate: float = 0.006
    use_empirical_transitions: bool = False
    transition_model_path: str = str(DEFAULT_TRANSITION_MODEL_PATH)
    runner_advancement_model: str = "empirical_speed_attempt"
    speed_attempt_model_path: str = str(DEFAULT_SPEED_ATTEMPT_MODEL_PATH)
    speed_attempt_model_names: tuple[str, ...] | None = None
    speed_attempt_stats: SpeedAttemptStats | None = None
    min_speed_multiplier: float = 0.50
    max_speed_multiplier: float = 1.75
    steal_attempt_prior_rate: float = 0.035
    steal_attempt_prior_pa: float = 100.0
    steal_success_prior_attempts: float = 20.0
    steal_third_success_prior_attempts: float = 60.0
    default_gb_share: float = 0.45
    default_fb_share: float = 0.32
    default_ld_share: float = 0.18
    default_popup_share: float = 0.05
    steal_attempt_multiplier: float = 1.0
    steal_third_attempt_multiplier: float = 0.20
    default_steal_success_rate: float = 0.75
    max_steal_attempt_rate: float = 0.35
    use_contextual_walks: bool = False
    contextual_walk_model_path: str = str(DEFAULT_CONTEXTUAL_WALK_MODEL_PATH)


@dataclass(frozen=True)
class RunnerBaseState:
    """Base/out state preserving runner identities for speed-aware future models."""

    first: HitterProfile | None = None
    second: HitterProfile | None = None
    third: HitterProfile | None = None
    outs: int = 0

    @property
    def has_runner(self) -> bool:
        return self.first is not None or self.second is not None or self.third is not None


@dataclass(frozen=True)
class PlayResult:
    """Result of a steal attempt or completed plate appearance."""

    state: RunnerBaseState
    runs: int = 0
    plate_appearance_completed: bool = True


@dataclass(frozen=True)
class OneRunTrialResult:
    """One fresh-inning trial for the one-run probability mode."""

    success: bool
    plate_appearances: int
    first_run_outs: int | None
    sb_attempts: int
    sb: int
    cs: int
    final_outs: int
    batting_slots_completed: tuple[int, ...]


@dataclass(frozen=True)
class OneRunProbabilityResult:
    """Monte Carlo estimate for P(score at least once before three outs)."""

    trials: int
    successes: int
    failures: int
    probability: float
    standard_error: float
    ci95_low: float
    ci95_high: float
    average_pa_per_trial: float
    first_run_out_0_probability: float
    first_run_out_1_probability: float
    first_run_out_2_probability: float
    sb_attempts_per_trial: float
    sb_per_trial: float
    cs_per_trial: float
    seed: int | None



def expected_one_run_probability_plan(
    lineup: Sequence[HitterProfile],
    trials: int = 100_000,
    seed: int | None = 202503,
    max_plate_appearances_per_trial: int = 60,
    config: PlanEngineConfig | None = None,
) -> OneRunProbabilityResult:
    """Estimate P(score >= 1 before three outs from a fresh inning.

    Version A is descriptive behavior: bases empty, zero outs, batting slot 1,
    late-inning tie context, normal production steals and advancement, and the
    trial stops immediately once the first run scores.
    """

    _validate_lineup(lineup)
    if trials <= 0:
        raise ValueError("trials must be positive.")

    rng = np.random.default_rng(seed)
    model_config = config or PlanEngineConfig(use_empirical_transitions=True)
    results = [
        simulate_one_run_trial(
            lineup,
            rng,
            max_plate_appearances=max_plate_appearances_per_trial,
            config=model_config,
        )
        for _ in range(trials)
    ]
    successes = sum(1 for result in results if result.success)
    failures = trials - successes
    probability = successes / trials
    standard_error = float(np.sqrt(probability * (1.0 - probability) / trials))
    first_run_outs = {outs: sum(1 for result in results if result.first_run_outs == outs) for outs in (0, 1, 2)}
    return OneRunProbabilityResult(
        trials=trials,
        successes=successes,
        failures=failures,
        probability=float(probability),
        standard_error=standard_error,
        ci95_low=float(max(0.0, probability - 1.96 * standard_error)),
        ci95_high=float(min(1.0, probability + 1.96 * standard_error)),
        average_pa_per_trial=float(np.mean([result.plate_appearances for result in results])),
        first_run_out_0_probability=float(first_run_outs[0] / trials),
        first_run_out_1_probability=float(first_run_outs[1] / trials),
        first_run_out_2_probability=float(first_run_outs[2] / trials),
        sb_attempts_per_trial=float(np.mean([result.sb_attempts for result in results])),
        sb_per_trial=float(np.mean([result.sb for result in results])),
        cs_per_trial=float(np.mean([result.cs for result in results])),
        seed=seed,
    )


def simulate_one_run_trial(
    lineup: Sequence[HitterProfile],
    rng: np.random.Generator,
    max_plate_appearances: int = 60,
    config: PlanEngineConfig | None = None,
) -> OneRunTrialResult:
    """Simulate one fresh inning and stop at the first run or third out."""

    _validate_lineup(lineup)
    model_config = config or PlanEngineConfig(use_empirical_transitions=True)
    state = RunnerBaseState()
    batter_index = 0
    completed_plate_appearances = 0
    sb_attempts = 0
    sb = 0
    cs = 0
    slots: list[int] = []

    while state.outs < 3:
        if completed_plate_appearances > max_plate_appearances:
            raise RuntimeError("One-run trial exceeded max_plate_appearances.")

        hitter = lineup[batter_index % len(lineup)]
        before_steal = state
        steal_result = apply_pre_pa_steal(state, rng, model_config)
        attempt, safe, caught = _steal_counts(before_steal, steal_result.state)
        sb_attempts += attempt
        sb += safe
        cs += caught
        if steal_result.runs > 0:
            return OneRunTrialResult(True, completed_plate_appearances, before_steal.outs, sb_attempts, sb, cs, steal_result.state.outs, tuple(slots))
        state = steal_result.state
        if state.outs >= 3 and not steal_result.plate_appearance_completed:
            return OneRunTrialResult(False, completed_plate_appearances, None, sb_attempts, sb, cs, state.outs, tuple(slots))

        on_deck = lineup[(batter_index + 1) % len(lineup)]
        outcome = sample_plan_outcome(
            hitter,
            rng,
            model_config,
            state=state,
            on_deck=on_deck,
            inning=7,
            score_diff=0.0,
        )
        play = apply_plan_plate_appearance(state, hitter, outcome, rng, model_config)
        slots.append((batter_index % len(lineup)) + 1)
        completed_plate_appearances += 1
        if play.runs > 0:
            return OneRunTrialResult(True, completed_plate_appearances, state.outs, sb_attempts, sb, cs, play.state.outs, tuple(slots))
        state = play.state
        batter_index += 1

    return OneRunTrialResult(False, completed_plate_appearances, None, sb_attempts, sb, cs, state.outs, tuple(slots))


def _steal_counts(before: RunnerBaseState, after: RunnerBaseState) -> tuple[int, int, int]:
    if before == after:
        return 0, 0, 0
    if after.outs > before.outs:
        return 1, 0, 1
    return 1, 1, 0


def expected_runs_plan(
    lineup: Sequence[HitterProfile],
    games: int = 10_000,
    seed: int | None = 202503,
    innings_per_game: int = 9,
    max_plate_appearances_per_game: int = 500,
    config: PlanEngineConfig | None = None,
) -> SimulationResult:
    """Estimate expected runs/game with the plan-aligned engine."""

    _validate_lineup(lineup)
    if games <= 0:
        raise ValueError("games must be positive.")
    if innings_per_game <= 0:
        raise ValueError("innings_per_game must be positive.")

    rng = np.random.default_rng(seed)
    model_config = config or PlanEngineConfig(use_empirical_transitions=True)
    runs = np.array(
        [
            simulate_game_plan(
                lineup,
                rng,
                innings=innings_per_game,
                max_plate_appearances=max_plate_appearances_per_game,
                config=model_config,
            )
            for _ in range(games)
        ],
        dtype=float,
    )
    return SimulationResult(
        runs_per_game=float(runs.mean()),
        games=games,
        innings_per_game=innings_per_game,
        seed=seed,
        run_std=float(runs.std(ddof=1)) if games > 1 else 0.0,
        run_min=int(runs.min()),
        run_max=int(runs.max()),
    )


def simulate_game_plan(
    lineup: Sequence[HitterProfile],
    rng: np.random.Generator,
    innings: int = 9,
    max_plate_appearances: int = 500,
    config: PlanEngineConfig | None = None,
) -> int:
    """Simulate one nine-inning offensive game."""

    _validate_lineup(lineup)
    model_config = config or PlanEngineConfig(use_empirical_transitions=True)
    runs = 0
    batter_index = 0
    completed_plate_appearances = 0

    for _inning in range(innings):
        state = RunnerBaseState()
        while state.outs < 3:
            if completed_plate_appearances > max_plate_appearances:
                raise RuntimeError("Simulation exceeded max_plate_appearances.")

            hitter = lineup[batter_index % len(lineup)]
            steal_result = apply_pre_pa_steal(state, rng, model_config)
            runs += steal_result.runs
            state = steal_result.state
            if state.outs >= 3 and not steal_result.plate_appearance_completed:
                continue

            on_deck = lineup[(batter_index + 1) % len(lineup)]
            outcome = sample_plan_outcome(hitter, rng, model_config, state=state, on_deck=on_deck, inning=_inning + 1)
            play = apply_plan_plate_appearance(state, hitter, outcome, rng, model_config)
            runs += play.runs
            state = play.state
            batter_index += 1
            completed_plate_appearances += 1

    return runs


def plan_probabilities(hitter: HitterProfile, config: PlanEngineConfig | None = None) -> dict[str, float]:
    """Build plan event probabilities from a hitter profile and metadata."""

    model_config = config or PlanEngineConfig()
    pa = _metadata_float(hitter, "pa")
    if pa <= 0:
        return _split_existing_probabilities(hitter, model_config)

    ibb = min(_metadata_float(hitter, "ibb"), _metadata_float(hitter, "bb"))
    sh = _metadata_float(hitter, "sh")
    denominator = max(pa - ibb - sh, 1.0)

    counts = {
        "bb": max(_metadata_float(hitter, "bb") - ibb, 0.0),
        "hbp": _metadata_float(hitter, "hbp"),
        "single": _metadata_float(hitter, "single"),
        "double": _metadata_float(hitter, "double"),
        "triple": _metadata_float(hitter, "triple"),
        "hr": _metadata_float(hitter, "hr"),
        "k": _metadata_float(hitter, "k"),
    }
    known = sum(counts.values())
    out_count = max(denominator - known, 0.0)
    out_shares = _batted_out_shares(hitter, model_config)
    counts["gb_out"] = out_count * out_shares["gb_out"]
    counts["fb_out"] = out_count * out_shares["fb_out"]
    counts["ld_out"] = out_count * out_shares["ld_out"]
    counts["popup_out"] = out_count * out_shares["popup_out"]

    probabilities = {outcome: counts[outcome] / denominator for outcome in PLAN_OUTCOMES}
    return _normalize_probabilities(probabilities)


def sample_plan_outcome(
    hitter: HitterProfile,
    rng: np.random.Generator,
    config: PlanEngineConfig | None = None,
    state: RunnerBaseState | None = None,
    on_deck: HitterProfile | None = None,
    inning: int = 1,
    score_diff: float | None = None,
) -> str:
    model_config = config or PlanEngineConfig()
    probabilities = plan_probabilities(hitter, model_config)
    if model_config.use_contextual_walks and state is not None and on_deck is not None:
        contextual_model = load_contextual_walk_model(model_config.contextual_walk_model_path)
        if contextual_model is not None:
            p_walk = contextual_model.predict_probability(
                _profile_mlbam_id(hitter),
                _profile_mlbam_id(on_deck),
                _state_base_string(state),
                state.outs,
                inning,
                score_diff=score_diff,
            )
            if rng.random() < p_walk:
                return "bb"
            non_walk = {outcome: probability for outcome, probability in probabilities.items() if outcome != "bb"}
            total = sum(non_walk.values())
            if total > 0:
                outcomes = [outcome for outcome in PLAN_OUTCOMES if outcome != "bb"]
                return str(rng.choice(outcomes, p=[non_walk[outcome] / total for outcome in outcomes]))
    return str(rng.choice(PLAN_OUTCOMES, p=[probabilities[outcome] for outcome in PLAN_OUTCOMES]))


def apply_pre_pa_steal(
    state: RunnerBaseState,
    rng: np.random.Generator,
    config: PlanEngineConfig,
) -> PlayResult:
    """Apply at most one steal attempt before the PA, preserving batter index."""

    if state.first is not None and state.second is None:
        return _attempt_steal(state, "second", state.first, rng, config)
    if state.first is None and state.second is not None and state.third is None:
        return _attempt_steal(state, "third", state.second, rng, config)
    return PlayResult(state=state, plate_appearance_completed=True)


def apply_plan_plate_appearance(
    state: RunnerBaseState,
    batter: HitterProfile,
    outcome: str,
    rng: np.random.Generator,
    config: PlanEngineConfig | None = None,
) -> PlayResult:
    """Resolve a completed PA outcome into runs/base/out state."""

    model_config = config or PlanEngineConfig()
    if outcome in {"bb", "hbp"}:
        return _apply_walk_or_hbp(state, batter)
    if outcome == "single":
        return _apply_single(state, batter, rng, model_config)
    if outcome == "double":
        return _apply_double(state, batter, rng, model_config)
    if outcome == "triple":
        return PlayResult(RunnerBaseState(third=batter, outs=state.outs), runs=_occupied_count(state))
    if outcome == "hr":
        return PlayResult(RunnerBaseState(outs=state.outs), runs=_occupied_count(state) + 1)
    if outcome == "k":
        return PlayResult(_with_outs(state, state.outs + 1))
    if outcome == "gb_out":
        return _apply_groundout(state, batter, rng, model_config)
    if outcome == "fb_out":
        return _apply_flyout(state, batter, rng, model_config)
    if outcome == "ld_out":
        return _apply_lineout(state, batter, rng, model_config)
    if outcome == "popup_out":
        return PlayResult(_with_outs(state, state.outs + 1))
    raise ValueError(f"Unsupported plan outcome: {outcome}")


def _apply_walk_or_hbp(state: RunnerBaseState, batter: HitterProfile) -> PlayResult:
    runs = 0
    first = state.first
    second = state.second
    third = state.third
    if first is None:
        first = batter
    elif second is None:
        second = first
        first = batter
    elif third is None:
        third = second
        second = first
        first = batter
    else:
        runs = 1
        third = second
        second = first
        first = batter
    return PlayResult(RunnerBaseState(first=first, second=second, third=third, outs=state.outs), runs=runs)


def _apply_single(state: RunnerBaseState, batter: HitterProfile, rng: np.random.Generator, config: PlanEngineConfig) -> PlayResult:
    empirical = _sample_empirical_transition(state, batter, "single", "single_detail", rng, config)
    if empirical is not None:
        return _apply_empirical_transition(state, batter, empirical)

    runs = 0
    outs = state.outs
    first = batter
    second = state.first
    third = None

    if state.third is not None:
        runs += 1

    second_cleared = False
    if state.second is not None:
        decision = _sample_transition(config.second_to_home_on_single, rng)
        if decision == "advance":
            runs += 1
            second_cleared = True
        elif decision == "out":
            outs += 1
            second_cleared = True
        else:
            third = state.second

    if state.first is not None:
        can_try = state.second is None or second_cleared
        if can_try and outs < 3:
            decision = _sample_transition(_runner_adjusted_probabilities(config.first_to_third_on_single, state.first, config), rng)
            if decision == "advance":
                second = None
                third = state.first
            elif decision == "out":
                second = None
                outs += 1
        elif second is None:
            second = state.first

    return PlayResult(RunnerBaseState(first=first, second=second, third=third, outs=min(outs, 3)), runs=runs)


def _apply_double(state: RunnerBaseState, batter: HitterProfile, rng: np.random.Generator, config: PlanEngineConfig) -> PlayResult:
    empirical = _sample_empirical_transition(state, batter, "double", None, rng, config)
    if empirical is not None:
        return _apply_empirical_transition(state, batter, empirical)

    runs = int(state.third is not None) + int(state.second is not None)
    outs = state.outs
    third = None
    if state.first is not None:
        decision = _sample_transition(_runner_adjusted_probabilities(config.first_to_home_on_double, state.first, config), rng)
        if decision == "advance":
            runs += 1
        elif decision == "out":
            outs += 1
        else:
            third = state.first
    return PlayResult(RunnerBaseState(second=batter, third=third, outs=min(outs, 3)), runs=runs)


def _apply_groundout(state: RunnerBaseState, batter: HitterProfile, rng: np.random.Generator, config: PlanEngineConfig) -> PlayResult:
    empirical = _sample_empirical_transition(state, batter, "gb_out", "gb_location", rng, config)
    if empirical is not None:
        return _apply_empirical_transition(state, batter, empirical)

    if state.outs >= 2 or not state.has_runner:
        return PlayResult(_with_outs(RunnerBaseState(outs=state.outs), state.outs + 1))
    if state.first is not None:
        double_play_rate = float(np.clip(config.groundout_double_play_rate * _double_play_multiplier(batter, config), 0.0, 0.95))
        if rng.random() < double_play_rate:
            return PlayResult(_with_outs(RunnerBaseState(outs=state.outs), state.outs + 2))

    runs = 0
    outs = state.outs + 1
    first = batter if state.first is not None else None
    second = None
    third = None

    if state.third is not None:
        decision = _sample_transition(config.third_to_home_on_groundout, rng)
        if decision == "advance":
            runs += 1
        elif decision == "out":
            outs += 1
            first = batter
        else:
            third = state.third

    if state.second is not None and outs < 3:
        can_try = state.third is None or third is None
        if can_try:
            decision = _sample_transition(config.second_to_third_on_groundout, rng)
            if decision == "advance":
                third = state.second
            elif decision == "out":
                outs += 1
                first = batter
            else:
                second = state.second
        else:
            second = state.second

    return PlayResult(RunnerBaseState(first=first if outs < 3 else None, second=second, third=third, outs=min(outs, 3)), runs=runs)


def _apply_flyout(state: RunnerBaseState, batter: HitterProfile | None, rng: np.random.Generator, config: PlanEngineConfig) -> PlayResult:
    empirical = _sample_empirical_transition(state, batter, "fb_out", "flyout_detail", rng, config) if batter is not None else None
    if empirical is not None:
        return _apply_empirical_transition(state, batter, empirical)

    if state.outs >= 2:
        return PlayResult(_with_outs(RunnerBaseState(outs=state.outs), state.outs + 1))
    runs = 0
    outs = state.outs + 1
    first = state.first
    second = state.second
    third = state.third

    if state.third is not None:
        decision = _sample_transition(config.third_to_home_on_flyout, rng)
        if decision == "advance":
            runs += 1
            third = None
        elif decision == "out":
            outs += 1
            third = None

    if state.second is not None and outs < 3 and third is None:
        decision = _sample_transition(config.second_to_third_on_flyout, rng)
        if decision == "advance":
            second = None
            third = state.second
        elif decision == "out":
            second = None
            outs += 1

    return PlayResult(RunnerBaseState(first=first, second=second, third=third, outs=min(outs, 3)), runs=runs)


def _apply_lineout(state: RunnerBaseState, batter: HitterProfile | None, rng: np.random.Generator, config: PlanEngineConfig) -> PlayResult:
    empirical = _sample_empirical_transition(state, batter, "ld_out", None, rng, config) if batter is not None else None
    if empirical is not None:
        return _apply_empirical_transition(state, batter, empirical)

    outs = state.outs + 1
    if state.has_runner and outs < 3 and rng.random() < config.lineout_doubleoff_rate:
        outs += 1
        if state.first is not None:
            return PlayResult(RunnerBaseState(second=state.second, third=state.third, outs=min(outs, 3)))
        if state.second is not None:
            return PlayResult(RunnerBaseState(first=state.first, third=state.third, outs=min(outs, 3)))
        return PlayResult(RunnerBaseState(first=state.first, second=state.second, outs=min(outs, 3)))
    return PlayResult(_with_outs(state, outs))


def _attempt_steal(state: RunnerBaseState, target_base: str, runner: HitterProfile, rng: np.random.Generator, config: PlanEngineConfig) -> PlayResult:
    base_state = _state_base_string(state)
    attempt_rate = _steal_attempt_rate(runner, config, target_base, base_state=base_state, outs=state.outs)
    if rng.random() >= attempt_rate:
        return PlayResult(state=state, plate_appearance_completed=True)

    if rng.random() < _steal_success_rate(runner, config, target_base, base_state=base_state, outs=state.outs):
        if target_base == "second":
            return PlayResult(RunnerBaseState(second=runner, third=state.third, outs=state.outs), plate_appearance_completed=True)
        return PlayResult(RunnerBaseState(first=state.first, third=runner, outs=state.outs), plate_appearance_completed=True)

    outs = state.outs + 1
    if target_base == "second":
        new_state = RunnerBaseState(second=state.second, third=state.third, outs=min(outs, 3))
    else:
        new_state = RunnerBaseState(first=state.first, third=state.third, outs=min(outs, 3))
    return PlayResult(new_state, plate_appearance_completed=outs < 3)


def _sample_transition(probabilities: CategoricalProbabilities, rng: np.random.Generator) -> str:
    return str(rng.choice(("hold", "advance", "out"), p=[probabilities.hold, probabilities.advance, probabilities.out]))


def _sample_empirical_transition(
    state: RunnerBaseState,
    batter: HitterProfile | None,
    event: str,
    distribution_name: str | None,
    rng: np.random.Generator,
    config: PlanEngineConfig,
) -> EmpiricalTransition | None:
    model = _transition_model(config)
    if model is None:
        return None
    detail = None
    if distribution_name is not None and batter is not None:
        detail = model.sample_detail(_profile_mlbam_id(batter), distribution_name, rng)
    if config.runner_advancement_model == "empirical_speed_attempt":
        origin_multipliers = {}
        attempt_adjustments = _speed_attempt_adjustments(state, event, detail, config)
    else:
        origin_multipliers = _origin_speed_multipliers(state, config)
        attempt_adjustments = []
    return model.sample_transition(
        event,
        state.outs,
        _state_base_string(state),
        detail,
        rng,
        origin_multipliers=origin_multipliers,
        attempt_adjustments=attempt_adjustments,
        double_play_multiplier=_double_play_multiplier(batter, config) if batter is not None else 1.0,
    )


def _apply_empirical_transition(
    state: RunnerBaseState,
    batter: HitterProfile | None,
    transition: EmpiricalTransition,
) -> PlayResult:
    destinations = {
        "third": (state.third, transition.third),
        "second": (state.second, transition.second),
        "first": (state.first, transition.first),
        "batter": (batter, transition.batter),
    }
    new_bases: dict[str, HitterProfile | None] = {"first": None, "second": None, "third": None}
    for _origin, (runner, destination) in destinations.items():
        if runner is None or destination not in new_bases:
            continue
        if new_bases[destination] is None:
            new_bases[destination] = runner
    outs = min(state.outs + max(int(transition.outs_added), 0), 3)
    if outs >= 3:
        return PlayResult(RunnerBaseState(outs=3), runs=max(int(transition.runs), 0))
    return PlayResult(
        RunnerBaseState(
            first=new_bases["first"],
            second=new_bases["second"],
            third=new_bases["third"],
            outs=outs,
        ),
        runs=max(int(transition.runs), 0),
    )


def transition_model_summary(config: PlanEngineConfig | None = None) -> dict[str, object]:
    """Return the loaded empirical transition model summary for UI/reporting."""

    model = _transition_model(config or PlanEngineConfig(use_empirical_transitions=True))
    if model is None:
        return {"loaded": False}
    return {"loaded": True, **model.model_summary()}


def _transition_model(config: PlanEngineConfig) -> TransitionModel | None:
    if not config.use_empirical_transitions:
        return None
    return load_transition_model(config.transition_model_path)


def _state_base_string(state: RunnerBaseState) -> str:
    return base_state_from_occupancy(state.first, state.second, state.third)


def _profile_mlbam_id(hitter: HitterProfile) -> object:
    return hitter.metadata.get("mlbam_id") or hitter.metadata.get("batter") or hitter.player_id


def _runner_adjusted_probabilities(
    probabilities: CategoricalProbabilities,
    runner: HitterProfile,
    config: PlanEngineConfig,
) -> CategoricalProbabilities:
    if config.runner_advancement_model == "empirical_speed_attempt":
        return probabilities
    multiplier = _runner_speed_multiplier(runner, config)
    advance = min(probabilities.advance * multiplier, 1.0 - probabilities.out)
    hold = max(0.0, 1.0 - advance - probabilities.out)
    return CategoricalProbabilities(hold=hold, advance=advance, out=probabilities.out)


def _runner_speed_multiplier(runner: HitterProfile, config: PlanEngineConfig) -> float:
    sprint_speed = _metadata_optional_float(runner, "sprint_speed")
    if sprint_speed is not None:
        return float(
            np.clip(
                1.0 + ((sprint_speed - 27.0) * 0.07),
                config.min_speed_multiplier,
                config.max_speed_multiplier,
            )
        )
    return 1.0


def _origin_speed_multipliers(state: RunnerBaseState, config: PlanEngineConfig) -> dict[str, float]:
    multipliers: dict[str, float] = {}
    if state.first is not None:
        multipliers["first"] = _runner_speed_multiplier(state.first, config)
    if state.second is not None:
        multipliers["second"] = _runner_speed_multiplier(state.second, config)
    if state.third is not None:
        multipliers["third"] = _runner_speed_multiplier(state.third, config)
    return multipliers



def _speed_attempt_adjustments(
    state: RunnerBaseState,
    event: str,
    detail: str | None,
    config: PlanEngineConfig,
) -> list[dict[str, object]]:
    speed_model = load_speed_attempt_model(config.speed_attempt_model_path)
    if speed_model is None:
        return []
    adjustments: list[dict[str, object]] = []
    allowed = set(config.speed_attempt_model_names) if config.speed_attempt_model_names is not None else None
    for origin, runner in (("first", state.first), ("second", state.second), ("third", state.third)):
        if runner is None:
            continue
        spec = speed_model.spec_for_context(event, origin, state.outs, detail)
        if spec is None:
            continue
        if allowed is not None and spec.name not in allowed:
            continue
        if config.speed_attempt_stats is not None:
            config.speed_attempt_stats.record_opportunity(spec.name)
        sprint_speed = _metadata_optional_float(runner, "sprint_speed")
        if sprint_speed is None:
            sprint_speed = speed_model.neutral_sprint_speed
            if config.speed_attempt_stats is not None:
                config.speed_attempt_stats.record_neutral_fallback(spec.name)
        p_actual = speed_model.predict(spec.name, sprint_speed, state.outs, detail)
        p_neutral = speed_model.predict(spec.name, speed_model.neutral_sprint_speed, state.outs, detail)
        if p_actual is None or p_neutral is None:
            if config.speed_attempt_stats is not None:
                config.speed_attempt_stats.record_neutral_fallback(spec.name)
            continue
        adjustments.append(
            {
                "model_name": spec.name,
                "origin": spec.origin,
                "attempt_destinations": spec.attempt_destinations,
                "no_attempt_destinations": spec.no_attempt_destinations,
                "p_actual": p_actual,
                "p_neutral": p_neutral,
            }
        )
    return adjustments


def _double_play_multiplier(batter: HitterProfile, config: PlanEngineConfig) -> float:
    home_to_first = _metadata_optional_float(batter, "home_to_first")
    if home_to_first is not None:
        return _fitted_gdp_home_to_first_multiplier(home_to_first)
    sprint_speed = _metadata_optional_float(batter, "sprint_speed")
    if sprint_speed is not None:
        return float(np.clip(1.0 - ((sprint_speed - 27.0) * 0.05), 0.60, 1.50))
    pa = _metadata_float(batter, "pa")
    rdp = _metadata_optional_float(batter, "rdp")
    gdp_runs = _metadata_optional_float(batter, "gdp_runs")
    if rdp is not None and pa > 0:
        return float(np.clip(1.0 - ((rdp * 600.0 / pa) * 0.035), 0.60, 1.50))
    if gdp_runs is not None and pa > 0:
        return float(np.clip(1.0 - ((gdp_runs * 600.0 / pa) * 0.035), 0.60, 1.50))
    return 1.0


def _fitted_gdp_home_to_first_multiplier(home_to_first: float) -> float:
    ht1 = float(np.clip(home_to_first, FITTED_GDP_MIN_HOME_TO_FIRST, FITTED_GDP_MAX_HOME_TO_FIRST))
    actual = _fitted_gdp_probability(ht1)
    neutral = _fitted_gdp_probability(FITTED_GDP_NEUTRAL_HOME_TO_FIRST)
    if neutral <= 0:
        return 1.0
    return float(np.clip(actual / neutral, FITTED_GDP_MIN_MULTIPLIER, FITTED_GDP_MAX_MULTIPLIER))


def _fitted_gdp_probability(home_to_first: float) -> float:
    z = (float(home_to_first) - FITTED_GDP_HT1_MEAN) / FITTED_GDP_HT1_SCALE
    logit = FITTED_GDP_HT1_INTERCEPT + FITTED_GDP_HT1_COEFFICIENT * z
    return float(1.0 / (1.0 + np.exp(-logit)))


def _split_existing_probabilities(hitter: HitterProfile, config: PlanEngineConfig) -> dict[str, float]:
    probabilities = {outcome: hitter.probabilities.get(outcome, 0.0) for outcome in PLAN_OUTCOMES}
    if sum(probabilities.values()) > 0:
        return _normalize_probabilities(probabilities)
    base = {outcome: hitter.probabilities.get(outcome, 0.0) for outcome in ("bb", "hbp", "single", "double", "triple", "hr", "k")}
    other_out = hitter.probabilities.get("other_out", 0.0)
    shares = _batted_out_shares(hitter, config)
    base.update({outcome: other_out * shares[outcome] for outcome in ("gb_out", "fb_out", "ld_out", "popup_out")})
    return _normalize_probabilities(base)


def _batted_out_shares(hitter: HitterProfile, config: PlanEngineConfig) -> dict[str, float]:
    gb_count = _metadata_float(hitter, "gb_count")
    fb_count = _metadata_float(hitter, "fb_count")
    ld_count = _metadata_float(hitter, "ld_count")
    popup_count = _metadata_float(hitter, "popup_count")
    if gb_count + fb_count + ld_count + popup_count > 0:
        raw = {"gb_out": gb_count, "fb_out": max(fb_count - popup_count, 0.0), "ld_out": ld_count, "popup_out": popup_count}
    else:
        gb = _metadata_optional_float(hitter, "gb_rate")
        fb = _metadata_optional_float(hitter, "fb_rate")
        ld = _metadata_optional_float(hitter, "ld_rate")
        popup = _metadata_optional_float(hitter, "popup_rate")
        if popup is None:
            popup = config.default_popup_share
        if gb is None or fb is None or ld is None:
            raw = {
                "gb_out": config.default_gb_share,
                "fb_out": config.default_fb_share,
                "ld_out": config.default_ld_share,
                "popup_out": config.default_popup_share,
            }
        else:
            if popup > 1:
                popup /= 100.0
            raw = {"gb_out": gb, "fb_out": max(fb - popup, 0.0), "ld_out": ld, "popup_out": popup}
    total = sum(raw.values())
    if total <= 0:
        return {
            "gb_out": config.default_gb_share,
            "fb_out": config.default_fb_share,
            "ld_out": config.default_ld_share,
            "popup_out": config.default_popup_share,
        }
    return {key: value / total for key, value in raw.items()}


def _normalize_probabilities(probabilities: Mapping[str, float]) -> dict[str, float]:
    complete = {outcome: max(float(probabilities.get(outcome, 0.0)), 0.0) for outcome in PLAN_OUTCOMES}
    total = sum(complete.values())
    if total <= 0:
        raise ValueError("Plan probabilities must have positive mass.")
    return {outcome: value / total for outcome, value in complete.items()}


def _steal_attempt_rate(
    runner: HitterProfile,
    config: PlanEngineConfig,
    target_base: str = "second",
    base_state: str | None = None,
    outs: int | None = None,
) -> float:
    contextual = _contextual_steal_probability(runner, target_base, "attempt", base_state, outs)
    if contextual is not None:
        return float(np.clip(contextual * config.steal_attempt_multiplier, 0.0, config.max_steal_attempt_rate))

    attempts = _metadata_float(runner, "sb") + _metadata_float(runner, "cs")
    pa = _metadata_float(runner, "pa")
    if attempts > 0 and pa > 0:
        raw_rate = attempts / pa
        shrunk = ((raw_rate * pa) + (config.steal_attempt_prior_rate * config.steal_attempt_prior_pa)) / (pa + config.steal_attempt_prior_pa)
        if target_base == "third":
            shrunk *= config.steal_third_attempt_multiplier
        return float(np.clip(shrunk * config.steal_attempt_multiplier, 0.0, config.max_steal_attempt_rate))

    league = _league_contextual_steal_probability(target_base, "attempt", base_state, outs)
    if league is not None:
        return float(np.clip(league * config.steal_attempt_multiplier, 0.0, config.max_steal_attempt_rate))

    legacy = _legacy_standardized_steal_probability(runner, target_base, "attempt")
    if legacy is not None:
        return float(np.clip(legacy * config.steal_attempt_multiplier, 0.0, config.max_steal_attempt_rate))
    return 0.0


def _steal_success_rate(
    runner: HitterProfile,
    config: PlanEngineConfig,
    target_base: str = "second",
    base_state: str | None = None,
    outs: int | None = None,
) -> float:
    contextual = _contextual_steal_probability(runner, target_base, "success", base_state, outs)
    if contextual is not None:
        return float(np.clip(contextual, 0.0, 1.0))

    steals = _metadata_float(runner, "sb")
    caught = _metadata_float(runner, "cs")
    attempts = steals + caught
    prior_attempts = config.steal_third_success_prior_attempts if target_base == "third" else config.steal_success_prior_attempts
    prior_successes = config.default_steal_success_rate * prior_attempts
    if attempts > 0:
        return float(np.clip((steals + prior_successes) / (attempts + prior_attempts), 0.0, 1.0))

    league = _league_contextual_steal_probability(target_base, "success", base_state, outs)
    if league is not None:
        return float(np.clip(league, 0.0, 1.0))

    legacy = _legacy_standardized_steal_probability(runner, target_base, "success")
    if legacy is not None:
        return float(np.clip(legacy, 0.0, 1.0))
    return config.default_steal_success_rate


def _contextual_steal_probability(
    runner: HitterProfile,
    target_base: str,
    kind: str,
    base_state: str | None,
    outs: int | None,
) -> float | None:
    column = _contextual_steal_column(target_base, kind, base_state, outs)
    if column is not None:
        value = _metadata_optional_float(runner, column)
        if value is not None:
            return value
    payload = runner.metadata.get("stolen_base_context")
    if isinstance(payload, str) and payload.strip():
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = None
    if not isinstance(payload, Mapping):
        return None
    target_key = "3B" if target_base == "third" else "2B"
    if not isinstance(payload.get(target_key), Mapping) or base_state not in payload[target_key]:
        return None
    state_payload = payload[target_key][base_state]
    if not isinstance(state_payload, Mapping):
        return None
    value = state_payload.get(kind)
    if isinstance(value, Mapping):
        if outs is None:
            return None
        value = value.get(str(int(outs)))
    try:
        if value is None or np.isnan(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _contextual_steal_column(target_base: str, kind: str, base_state: str | None, outs: int | None) -> str | None:
    if target_base == "second":
        if kind == "success":
            if base_state == "1--":
                return "steal_2b_success_1xx"
            if base_state == "1-3":
                return "steal_2b_success_1x3"
        if kind == "attempt" and outs is not None:
            if base_state == "1--":
                return f"steal_2b_attempt_1xx_{int(outs)}"
            if base_state == "1-3":
                return f"steal_2b_attempt_1x3_{int(outs)}"
    if target_base == "third":
        if kind == "success" and base_state == "-2-":
            return "steal_3b_success_x2x"
        if kind == "attempt" and base_state == "-2-" and outs is not None:
            return f"steal_3b_attempt_x2x_{int(outs)}"
    return None


def _league_contextual_steal_probability(target_base: str, kind: str, base_state: str | None, outs: int | None) -> float | None:
    attempt_defaults = {
        ("second", "1--", 0): 0.075396,
        ("second", "1--", 1): 0.084103,
        ("second", "1--", 2): 0.092942,
        ("second", "1-3", 0): 0.082572,
        ("second", "1-3", 1): 0.091955,
        ("second", "1-3", 2): 0.101454,
        ("third", "-2-", 0): 0.005832,
        ("third", "-2-", 1): 0.022160,
        ("third", "-2-", 2): 0.010911,
    }
    success_defaults = {
        ("second", "1--"): 0.746588,
        ("second", "1-3"): 0.915400,
        ("third", "-2-"): 0.785033,
    }
    if kind == "attempt" and outs is not None:
        return attempt_defaults.get((target_base, base_state, int(outs)))
    if kind == "success":
        return success_defaults.get((target_base, base_state))
    return None


def _legacy_standardized_steal_probability(runner: HitterProfile, target_base: str, kind: str) -> float | None:
    base = "3b" if target_base == "third" else "2b"
    return _metadata_optional_float(runner, f"steal_{base}_{kind}_probability")


def _metadata_float(hitter: HitterProfile, key: str) -> float:
    value = _metadata_optional_float(hitter, key)
    return value if value is not None else 0.0


def _metadata_optional_float(hitter: HitterProfile, key: str) -> float | None:
    value = hitter.metadata.get(key)
    try:
        if value is None or bool(getattr(value, "isna", lambda: False)()):
            return None
    except TypeError:
        pass
    try:
        if np.isnan(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _occupied_count(state: RunnerBaseState) -> int:
    return sum(runner is not None for runner in (state.first, state.second, state.third))


def _with_outs(state: RunnerBaseState, outs: int) -> RunnerBaseState:
    if outs >= 3:
        return RunnerBaseState(outs=3)
    return RunnerBaseState(first=state.first, second=state.second, third=state.third, outs=outs)


def _validate_lineup(lineup: Sequence[HitterProfile]) -> None:
    if len(lineup) != 9:
        raise ValueError(f"Lineup must contain exactly 9 hitters, got {len(lineup)}.")
