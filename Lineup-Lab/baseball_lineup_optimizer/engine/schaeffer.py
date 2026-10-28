"""Schaeffer-style Monte Carlo engine with baserunning events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from baseball_lineup_optimizer.engine.outcomes import HitterProfile
from baseball_lineup_optimizer.engine.simulation import SimulationResult


SCHAEFFER_OUTCOMES = (
    "bb",
    "hbp",
    "single",
    "double",
    "triple",
    "hr",
    "k",
    "groundout",
    "airout",
)


@dataclass(frozen=True)
class ExtraBaseProbabilities:
    """No-attempt, success, and failure rates for one advancement choice."""

    no_attempt: float
    success: float
    failure: float


@dataclass(frozen=True)
class BaserunningConfig:
    """Configurable baserunning and error assumptions for the advanced engine."""

    first_to_third_on_single: ExtraBaseProbabilities = ExtraBaseProbabilities(0.638, 0.349, 0.013)
    second_to_home_on_single: ExtraBaseProbabilities = ExtraBaseProbabilities(0.352, 0.617, 0.031)
    first_to_home_on_double: ExtraBaseProbabilities = ExtraBaseProbabilities(0.635, 0.338, 0.027)
    second_to_third_on_airout: ExtraBaseProbabilities = ExtraBaseProbabilities(0.766, 0.221, 0.013)
    third_to_home_on_airout: ExtraBaseProbabilities = ExtraBaseProbabilities(0.391, 0.524, 0.085)
    second_to_third_on_groundout: ExtraBaseProbabilities = ExtraBaseProbabilities(0.315, 0.644, 0.041)
    third_to_home_on_groundout: ExtraBaseProbabilities = ExtraBaseProbabilities(0.138, 0.552, 0.310)
    error_rate_on_batted_out: float = 0.0059
    wild_pitch_passed_ball_balk_rate: float = 0.0216
    groundout_double_play_rate: float = 0.11
    min_groundout_double_play_rate: float = 0.03
    max_groundout_double_play_rate: float = 0.22
    gdp_runs_rate_adjustment_per_run_per_600_pa: float = 0.02
    league_gdp_per_pa: float = 0.0172
    gdp_fallback_multiplier_min: float = 0.50
    gdp_fallback_multiplier_max: float = 1.75
    default_groundout_share: float = 0.45
    default_steal_success_rate: float = 0.75
    max_steal_attempt_rate: float = 0.35
    steal_attempt_multiplier: float = 1.0
    league_xbt_rate: float = 0.41
    min_xbt_multiplier: float = 0.50
    max_xbt_multiplier: float = 1.75


@dataclass(frozen=True)
class RunnerBaseState:
    """Base/out state that preserves which hitter is occupying each base."""

    first: HitterProfile | None = None
    second: HitterProfile | None = None
    third: HitterProfile | None = None
    outs: int = 0

    @property
    def has_runner(self) -> bool:
        return self.first is not None or self.second is not None or self.third is not None


@dataclass(frozen=True)
class PlayResult:
    """State transition from one pre-PA or PA event."""

    state: RunnerBaseState
    runs: int = 0
    plate_appearance_completed: bool = True


def empty_runner_state() -> RunnerBaseState:
    """Create an empty inning state."""

    return RunnerBaseState()


def expected_runs_schaeffer(
    lineup: Sequence[HitterProfile],
    games: int = 10_000,
    seed: int | None = 202503,
    innings_per_game: int = 9,
    max_plate_appearances_per_game: int = 500,
    config: BaserunningConfig | None = None,
) -> SimulationResult:
    """Estimate runs using a Schaeffer-style event order and baserunning model."""

    _validate_lineup(lineup)
    if games <= 0:
        raise ValueError("games must be positive.")
    if innings_per_game <= 0:
        raise ValueError("innings_per_game must be positive.")

    rng = np.random.default_rng(seed)
    model_config = config or BaserunningConfig()
    runs = np.array(
        [
            simulate_game_schaeffer(
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


def simulate_game_schaeffer(
    lineup: Sequence[HitterProfile],
    rng: np.random.Generator,
    innings: int = 9,
    max_plate_appearances: int = 500,
    config: BaserunningConfig | None = None,
) -> int:
    """Simulate one game-equivalent with steals, extra-base attempts, and errors."""

    _validate_lineup(lineup)
    model_config = config or BaserunningConfig()
    runs = 0
    batter_index = 0
    plate_appearances = 0

    for _inning in range(innings):
        state = empty_runner_state()
        while state.outs < 3:
            plate_appearances += 1
            if plate_appearances > max_plate_appearances:
                raise RuntimeError(
                    "Simulation exceeded max_plate_appearances. "
                    "This usually means the lineup has too little out probability."
                )

            steal_result = apply_pre_plate_appearance_events(state, rng, model_config)
            runs += steal_result.runs
            state = steal_result.state
            if state.outs >= 3 and not steal_result.plate_appearance_completed:
                continue

            hitter = lineup[batter_index % len(lineup)]
            outcome = sample_schaeffer_outcome(hitter, rng, model_config)
            if outcome in {"groundout", "airout"} and rng.random() < model_config.error_rate_on_batted_out:
                outcome = "single"
            play_result = apply_plate_appearance(state, hitter, outcome, rng, model_config)
            runs += play_result.runs
            state = play_result.state
            batter_index += 1
    return runs


def sample_schaeffer_outcome(
    hitter: HitterProfile,
    rng: np.random.Generator,
    config: BaserunningConfig | None = None,
) -> str:
    """Sample a PA outcome after splitting other outs into ground and air outs."""

    probabilities = schaeffer_probabilities(hitter, config or BaserunningConfig())
    return str(rng.choice(SCHAEFFER_OUTCOMES, p=[probabilities[outcome] for outcome in SCHAEFFER_OUTCOMES]))


def schaeffer_probabilities(hitter: HitterProfile, config: BaserunningConfig | None = None) -> dict[str, float]:
    """Convert the MVP hitter profile into the advanced outcome set."""

    model_config = config or BaserunningConfig()
    probabilities = {
        outcome: hitter.probabilities[outcome]
        for outcome in ("bb", "hbp", "single", "double", "triple", "hr", "k")
    }
    other_out = hitter.probabilities["other_out"]
    ground_share = _groundout_share(hitter, model_config)
    probabilities["groundout"] = other_out * ground_share
    probabilities["airout"] = other_out * (1.0 - ground_share)
    return probabilities


def apply_pre_plate_appearance_events(
    state: RunnerBaseState,
    rng: np.random.Generator,
    config: BaserunningConfig | None = None,
) -> PlayResult:
    """Apply one possible steal and one possible wild pitch/passed ball/balk."""

    model_config = config or BaserunningConfig()
    steal_result = _attempt_steal_if_available(state, rng, model_config)
    state = steal_result.state
    runs = steal_result.runs
    if state.outs >= 3 and not steal_result.plate_appearance_completed:
        return PlayResult(state=state, runs=runs, plate_appearance_completed=False)

    if state.has_runner and rng.random() < model_config.wild_pitch_passed_ball_balk_rate:
        wild_result = _advance_all_runners_one_base(state)
        state = wild_result.state
        runs += wild_result.runs
    return PlayResult(state=state, runs=runs, plate_appearance_completed=True)


def apply_plate_appearance(
    state: RunnerBaseState,
    batter: HitterProfile,
    outcome: str,
    rng: np.random.Generator,
    config: BaserunningConfig | None = None,
) -> PlayResult:
    """Apply a Schaeffer-style plate appearance transition."""

    model_config = config or BaserunningConfig()
    if outcome in {"bb", "hbp"}:
        return _apply_walk_or_hbp(state, batter)
    if outcome == "single":
        return _apply_single(state, batter, rng, model_config)
    if outcome == "double":
        return _apply_double(state, batter, rng, model_config)
    if outcome == "triple":
        return PlayResult(
            RunnerBaseState(third=batter, outs=state.outs),
            runs=_occupied_count(state),
        )
    if outcome == "hr":
        return PlayResult(
            RunnerBaseState(outs=state.outs),
            runs=_occupied_count(state) + 1,
        )
    if outcome == "k":
        return PlayResult(_with_outs(state, state.outs + 1))
    if outcome == "groundout":
        return _apply_groundout(state, batter, rng, model_config)
    if outcome == "airout":
        return _apply_airout(state, batter, rng, model_config)
    raise ValueError(f"Unsupported Schaeffer outcome: {outcome}")


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
        runs += 1
        third = second
        second = first
        first = batter
    return PlayResult(RunnerBaseState(first=first, second=second, third=third, outs=state.outs), runs=runs)


def _apply_single(
    state: RunnerBaseState,
    batter: HitterProfile,
    rng: np.random.Generator,
    config: BaserunningConfig,
) -> PlayResult:
    runs = 0
    outs = state.outs
    first = batter
    second = state.first
    third = None

    if state.third is not None:
        runs += 1

    second_runner_scored_or_out = False
    if state.second is not None:
        decision = _sample_extra_base(_runner_adjusted_extra_base_probabilities(config.second_to_home_on_single, state.second, config), rng)
        if decision == "success":
            runs += 1
            second_runner_scored_or_out = True
        elif decision == "failure":
            outs += 1
            second_runner_scored_or_out = True
        else:
            third = state.second

    if state.first is not None:
        can_try_first_to_third = state.second is None or second_runner_scored_or_out
        if can_try_first_to_third:
            decision = _sample_extra_base(_runner_adjusted_extra_base_probabilities(config.first_to_third_on_single, state.first, config), rng)
            if decision == "success":
                second = None
                third = state.first
            elif decision == "failure":
                second = None
                outs += 1
        elif second is None:
            second = state.first

    return PlayResult(RunnerBaseState(first=first, second=second, third=third, outs=min(outs, 3)), runs=runs)


def _apply_double(
    state: RunnerBaseState,
    batter: HitterProfile,
    rng: np.random.Generator,
    config: BaserunningConfig,
) -> PlayResult:
    runs = 0
    outs = state.outs
    third = None

    if state.third is not None:
        runs += 1
    if state.second is not None:
        runs += 1
    if state.first is not None:
        decision = _sample_extra_base(_runner_adjusted_extra_base_probabilities(config.first_to_home_on_double, state.first, config), rng)
        if decision == "success":
            runs += 1
        elif decision == "failure":
            outs += 1
        else:
            third = state.first

    return PlayResult(RunnerBaseState(second=batter, third=third, outs=min(outs, 3)), runs=runs)


def _apply_groundout(
    state: RunnerBaseState,
    batter: HitterProfile,
    rng: np.random.Generator,
    config: BaserunningConfig,
) -> PlayResult:
    if state.outs >= 2 or not state.has_runner:
        return PlayResult(_with_outs(RunnerBaseState(outs=state.outs), state.outs + 1))

    if state.first is not None and _is_double_play_state(state) and rng.random() < double_play_rate(batter, config):
        return PlayResult(_with_outs(RunnerBaseState(third=None, outs=state.outs), state.outs + 2))

    runs = 0
    outs = state.outs + 1
    first = None
    second = None
    third = None
    batter_safe_on_fielders_choice = state.first is not None

    if state.third is not None:
        decision = _sample_extra_base(config.third_to_home_on_groundout, rng)
        if decision == "success":
            runs += 1
        elif decision == "failure":
            outs += 1
            batter_safe_on_fielders_choice = True
        else:
            third = state.third

    if state.second is not None and outs < 3:
        if state.third is None or third is None:
            decision = _sample_extra_base(config.second_to_third_on_groundout, rng)
            if decision == "success":
                third = state.second
            elif decision == "failure":
                outs += 1
                batter_safe_on_fielders_choice = True
            else:
                second = state.second
        else:
            second = state.second

    if batter_safe_on_fielders_choice and outs < 3:
        first = batter

    return PlayResult(RunnerBaseState(first=first, second=second, third=third, outs=min(outs, 3)), runs=runs)


def _apply_airout(
    state: RunnerBaseState,
    batter: HitterProfile,
    rng: np.random.Generator,
    config: BaserunningConfig,
) -> PlayResult:
    del batter
    if state.outs >= 2:
        return PlayResult(_with_outs(RunnerBaseState(outs=state.outs), state.outs + 1))

    runs = 0
    outs = state.outs + 1
    first = state.first
    second = state.second
    third = state.third

    if state.third is not None:
        decision = _sample_extra_base(config.third_to_home_on_airout, rng)
        if decision == "success":
            runs += 1
            third = None
        elif decision == "failure":
            outs += 1
            third = None

    if state.second is not None and outs < 3:
        can_try_second_to_third = state.third is None or third is None
        if can_try_second_to_third:
            decision = _sample_extra_base(config.second_to_third_on_airout, rng)
            if decision == "success":
                second = None
                third = state.second
            elif decision == "failure":
                second = None
                outs += 1

    return PlayResult(RunnerBaseState(first=first, second=second, third=third, outs=min(outs, 3)), runs=runs)


def _attempt_steal_if_available(
    state: RunnerBaseState,
    rng: np.random.Generator,
    config: BaserunningConfig,
) -> PlayResult:
    if state.first is not None and state.second is None:
        return _attempt_steal(state, "second", state.first, rng, config)
    if state.second is not None and state.third is None:
        return _attempt_steal(state, "third", state.second, rng, config)
    return PlayResult(state=state, plate_appearance_completed=True)


def _attempt_steal(
    state: RunnerBaseState,
    target_base: str,
    runner: HitterProfile,
    rng: np.random.Generator,
    config: BaserunningConfig,
) -> PlayResult:
    if rng.random() >= _steal_attempt_rate(runner, config, target_base):
        return PlayResult(state=state, plate_appearance_completed=True)

    success_rate = _steal_success_rate(runner, config, target_base)
    if rng.random() < success_rate:
        if target_base == "second":
            return PlayResult(RunnerBaseState(second=runner, third=state.third, outs=state.outs), plate_appearance_completed=True)
        return PlayResult(RunnerBaseState(first=state.first, third=runner, outs=state.outs), plate_appearance_completed=True)

    outs = state.outs + 1
    if target_base == "second":
        new_state = RunnerBaseState(second=state.second, third=state.third, outs=min(outs, 3))
    else:
        new_state = RunnerBaseState(first=state.first, third=state.third, outs=min(outs, 3))
    return PlayResult(
        state=new_state,
        plate_appearance_completed=outs < 3,
    )


def _advance_all_runners_one_base(state: RunnerBaseState) -> PlayResult:
    runs = 1 if state.third is not None else 0
    return PlayResult(
        RunnerBaseState(first=None, second=state.first, third=state.second, outs=state.outs),
        runs=runs,
    )


def _sample_extra_base(probabilities: ExtraBaseProbabilities, rng: np.random.Generator) -> str:
    return str(
        rng.choice(
            ("no_attempt", "success", "failure"),
            p=[probabilities.no_attempt, probabilities.success, probabilities.failure],
        )
    )


def _runner_adjusted_extra_base_probabilities(
    probabilities: ExtraBaseProbabilities,
    runner: HitterProfile,
    config: BaserunningConfig,
) -> ExtraBaseProbabilities:
    multiplier = _xbt_multiplier(runner, config)
    success = min(probabilities.success * multiplier, 1.0 - probabilities.failure)
    no_attempt = max(0.0, 1.0 - success - probabilities.failure)
    return ExtraBaseProbabilities(no_attempt=no_attempt, success=success, failure=probabilities.failure)


def _xbt_multiplier(runner: HitterProfile, config: BaserunningConfig) -> float:
    xbt_rate = _metadata_optional_float(runner, "xbt_rate")
    if xbt_rate is None or config.league_xbt_rate <= 0:
        return 1.0
    if xbt_rate > 1:
        xbt_rate = xbt_rate / 100.0
    return float(np.clip(xbt_rate / config.league_xbt_rate, config.min_xbt_multiplier, config.max_xbt_multiplier))


def double_play_rate(hitter: HitterProfile, config: BaserunningConfig | None = None) -> float:
    """Estimate a hitter-specific groundout double-play probability."""

    model_config = config or BaserunningConfig()
    rate = model_config.groundout_double_play_rate
    pa = _metadata_float(hitter, "pa")
    rdp = _metadata_optional_float(hitter, "rdp")
    gdp_runs = _metadata_optional_float(hitter, "gdp_runs")

    if rdp is not None and pa > 0:
        rdp_per_600_pa = rdp * 600.0 / pa
        rate -= rdp_per_600_pa * model_config.gdp_runs_rate_adjustment_per_run_per_600_pa
    elif gdp_runs is not None and pa > 0:
        gdp_runs_per_600_pa = gdp_runs * 600.0 / pa
        rate -= gdp_runs_per_600_pa * model_config.gdp_runs_rate_adjustment_per_run_per_600_pa
    else:
        gdp = _metadata_optional_float(hitter, "gdp")
        if gdp is not None and pa > 0 and model_config.league_gdp_per_pa > 0:
            gdp_per_pa = gdp / pa
            multiplier = np.clip(
                gdp_per_pa / model_config.league_gdp_per_pa,
                model_config.gdp_fallback_multiplier_min,
                model_config.gdp_fallback_multiplier_max,
            )
            rate *= float(multiplier)

    return float(
        np.clip(
            rate,
            model_config.min_groundout_double_play_rate,
            model_config.max_groundout_double_play_rate,
        )
    )


def _groundout_share(hitter: HitterProfile, config: BaserunningConfig) -> float:
    gb_rate = _metadata_float(hitter, "gb_rate")
    fb_rate = _metadata_float(hitter, "fb_rate")
    ld_rate = _metadata_float(hitter, "ld_rate")
    denominator = gb_rate + fb_rate + ld_rate
    if denominator <= 0:
        return config.default_groundout_share
    return float(np.clip(gb_rate / denominator, 0.0, 1.0))


def _steal_attempt_rate(runner: HitterProfile, config: BaserunningConfig, target_base: str = "second") -> float:
    standardized = _standardized_steal_probability(runner, target_base, "attempt")
    if standardized is not None:
        return float(np.clip(standardized * config.steal_attempt_multiplier, 0.0, config.max_steal_attempt_rate))
    attempts = _metadata_float(runner, "sb") + _metadata_float(runner, "cs")
    pa = _metadata_float(runner, "pa")
    if attempts <= 0 or pa <= 0:
        return 0.0
    return float(np.clip((attempts / pa) * config.steal_attempt_multiplier, 0.0, config.max_steal_attempt_rate))


def _steal_success_rate(runner: HitterProfile, config: BaserunningConfig, target_base: str = "second") -> float:
    standardized = _standardized_steal_probability(runner, target_base, "success")
    if standardized is not None:
        return float(np.clip(standardized, 0.0, 1.0))
    steals = _metadata_float(runner, "sb")
    caught = _metadata_float(runner, "cs")
    attempts = steals + caught
    if attempts <= 0:
        return config.default_steal_success_rate
    return float(np.clip(steals / attempts, 0.0, 1.0))


def _standardized_steal_probability(runner: HitterProfile, target_base: str, kind: str) -> float | None:
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


def _is_double_play_state(state: RunnerBaseState) -> bool:
    if state.outs >= 2 or state.first is None:
        return False
    if state.outs == 0:
        return True
    return state.third is not None


def _validate_lineup(lineup: Sequence[HitterProfile]) -> None:
    if len(lineup) != 9:
        raise ValueError(f"Lineup must contain exactly 9 hitters, got {len(lineup)}.")
