
"""Version B one-run sacrifice-bunt strategy model.

This module is intentionally separate from the production plan engine. It builds
an absorbing MDP around sampled production-engine transitions, then adds an
optional PA-level sacrifice-bunt action in the six approved base/out states.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import lgamma, log
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from baseball_lineup_optimizer.engine.outcomes import HitterProfile
from baseball_lineup_optimizer.engine.plan_engine import (
    PlanEngineConfig,
    PlayResult,
    RunnerBaseState,
    _profile_mlbam_id,
    _state_base_string,
    apply_plan_plate_appearance,
    apply_pre_pa_steal,
    sample_plan_outcome,
)

ELIGIBLE_BUNT_STATES: tuple[tuple[str, int], ...] = (
    ("1--", 0),
    ("1--", 1),
    ("-2-", 0),
    ("-2-", 1),
    ("12-", 0),
    ("12-", 1),
)
ALL_BASE_STATES: tuple[str, ...] = ("---", "1--", "-2-", "--3", "12-", "1-3", "-23", "123")
ALL_STATE_KEYS: tuple[tuple[str, int], ...] = tuple((base, outs) for outs in range(3) for base in ALL_BASE_STATES)
FAVORABLE_BUNT_CATEGORIES = {"credited_sacrifice", "bunt_hit_or_extra_base", "reached_or_advanced_on_error"}


@dataclass(frozen=True)
class MdpResult:
    player_id: object
    player_name: str
    no_bunt_probability: float
    optimized_probability: float
    iterations: int
    converged: bool
    policy: dict[tuple[str, int], str]
    decision_rows: list[dict[str, object]]
    values: dict[tuple[str, int], float]


@dataclass(frozen=True)
class MonteCarloPolicyResult:
    trials: int
    successes: int
    probability: float
    standard_error: float
    ci95_low: float
    ci95_high: float
    bunt_attempts_per_trial: float
    reached_eligible_per_trial: dict[str, float]


@dataclass(frozen=True)
class BuntModel:
    definition: str
    rows: pd.DataFrame
    terminal_distributions: dict[tuple[str, int], list[dict[str, object]]]
    global_terminal_distribution: list[dict[str, object]]
    branch_rates: dict[tuple[str, int], float]
    global_abandon_rate: float
    player_effects: dict[int, dict[str, float]]
    league_success_rate: float
    shrinkage_prior_strength: float
    abandonment_distributions: dict[tuple[str, int], list[dict[str, object]]] | None = None
    global_abandonment_distribution: list[dict[str, object]] | None = None
    abandonment_strategy: str = "normal_pa"
    shrinkage_prior_alpha: float | None = None
    shrinkage_prior_beta: float | None = None
    shrinkage_method: str = "beta_binomial_mle_fixed_mean"


def state_key(state: RunnerBaseState) -> tuple[str, int]:
    return (_state_base_string(state), int(state.outs))


def state_from_key(key: tuple[str, int], hitter: HitterProfile) -> RunnerBaseState:
    base_state, outs = key
    return RunnerBaseState(
        first=hitter if base_state[0] == "1" else None,
        second=hitter if base_state[1] == "2" else None,
        third=hitter if base_state[2] == "3" else None,
        outs=int(outs),
    )


def is_eligible_bunt_state(key: tuple[str, int]) -> bool:
    return key in ELIGIBLE_BUNT_STATES


def result_to_transition(result: PlayResult) -> tuple[str, tuple[str, int] | None]:
    if result.runs > 0:
        return "success", None
    if result.state.outs >= 3:
        return "failure", None
    return "state", state_key(result.state)


def normalize_counter(counter: Mapping[tuple[str, tuple[str, int] | None], float]) -> list[tuple[float, str, tuple[str, int] | None]]:
    total = float(sum(counter.values()))
    if total <= 0:
        raise ValueError("transition counter has no probability mass")
    return [(count / total, terminal, key) for (terminal, key), count in counter.items()]


def expected_from_distribution(
    distribution: list[tuple[float, str, tuple[str, int] | None]],
    values: Mapping[tuple[str, int], float],
) -> float:
    total = 0.0
    for probability, terminal, key in distribution:
        if terminal == "success":
            total += probability
        elif terminal == "state" and key is not None:
            total += probability * float(values[key])
    return float(total)


def fit_bunt_model(
    candidate_path: str | Path,
    runner_events_path: str | Path,
    definition: str = "A",
    shrinkage_method: str = "beta_binomial_mle_fixed_mean",
    abandonment_strategy: str = "normal_pa",
) -> BuntModel:
    rows = pd.read_csv(candidate_path)
    if definition.upper() == "A":
        rows = rows[rows["definition_a_any_bunt_action"].astype(bool)].copy()
    elif definition.upper() == "B":
        rows = rows[rows["definition_b_first_pitch_bunt"].astype(bool)].copy()
    else:
        raise ValueError("definition must be 'A' or 'B'")

    rows["batter"] = pd.to_numeric(rows["batter"], errors="coerce").astype("Int64")
    rows["start_outs"] = pd.to_numeric(rows["start_outs"], errors="coerce").astype(int)
    rows["abandoned_branch"] = rows["normal_swing_after_first_bunt"].astype(bool)
    rows["favorable_terminal"] = rows["reconciled_category"].isin(FAVORABLE_BUNT_CATEGORIES).astype(int)

    runner_events = pd.read_csv(
        runner_events_path,
        usecols=["game_pk", "at_bat_number", "runner_id", "end_base", "is_out"],
        low_memory=False,
    )
    runner_events["game_pk"] = pd.to_numeric(runner_events["game_pk"], errors="coerce").astype("Int64")
    runner_events["at_bat_number"] = pd.to_numeric(runner_events["at_bat_number"], errors="coerce").astype("Int64")
    runner_events["runner_id"] = pd.to_numeric(runner_events["runner_id"], errors="coerce").astype("Int64")
    candidate_keys = rows[["game_pk", "at_bat_number"]].drop_duplicates()
    runner_events = runner_events.merge(candidate_keys, on=["game_pk", "at_bat_number"], how="inner")
    grouped_runner_events = {key: group for key, group in runner_events.groupby(["game_pk", "at_bat_number"], dropna=False)}

    transitions = []
    for row in rows.itertuples(index=False):
        transition = _reconstruct_bunt_transition(row, grouped_runner_events.get((row.game_pk, row.at_bat_number)))
        transitions.append(transition)
    transition_frame = pd.DataFrame(transitions)
    rows = pd.concat([rows.reset_index(drop=True), transition_frame], axis=1)

    terminal_rows = rows[~rows["abandoned_branch"]].copy()
    if terminal_rows.empty:
        raise ValueError("No terminal bunt rows available after branch split")
    terminal_distributions: dict[tuple[str, int], list[dict[str, object]]] = {}
    for (base_state, outs), group in terminal_rows.groupby(["base_state", "start_outs"]):
        terminal_distributions[(str(base_state), int(outs))] = _compact_transition_rows(group)
    global_terminal_distribution = _compact_transition_rows(terminal_rows)

    abandoned_rows = rows[rows["abandoned_branch"]].copy()
    abandonment_distributions: dict[tuple[str, int], list[dict[str, object]]] = {}
    if not abandoned_rows.empty:
        for (base_state, outs), group in abandoned_rows.groupby(["base_state", "start_outs"]):
            abandonment_distributions[(str(base_state), int(outs))] = _compact_transition_rows(group)
        global_abandonment_distribution = _compact_transition_rows(abandoned_rows)
    else:
        global_abandonment_distribution = []

    branch_rates: dict[tuple[str, int], float] = {}
    for (base_state, outs), group in rows.groupby(["base_state", "start_outs"]):
        branch_rates[(str(base_state), int(outs))] = float(group["abandoned_branch"].mean())
    global_abandon_rate = float(rows["abandoned_branch"].mean())

    terminal_rows["favorable_terminal"] = terminal_rows["reconciled_category"].isin(FAVORABLE_BUNT_CATEGORIES).astype(int)
    league_success_rate = float(terminal_rows["favorable_terminal"].mean())
    player_counts = terminal_rows.groupby("batter").agg(
        attempts=("favorable_terminal", "size"),
        successes=("favorable_terminal", "sum"),
    )
    shrinkage_info = _estimate_beta_binomial_prior(
        player_counts["attempts"].to_numpy(),
        player_counts["successes"].to_numpy(),
        league_success_rate,
        method=shrinkage_method,
    )
    shrinkage = float(shrinkage_info["prior_strength"])
    effects: dict[int, dict[str, float]] = {}
    for batter, group in rows.groupby("batter"):
        terminal_group = terminal_rows[terminal_rows["batter"].eq(batter)]
        n = int(len(terminal_group))
        successes = int(terminal_group["favorable_terminal"].sum()) if n else 0
        posterior = (successes + shrinkage * league_success_rate) / (n + shrinkage) if n + shrinkage > 0 else league_success_rate
        effects[int(batter)] = {
            "bunt_attempts": int(len(group)),
            "terminal_bunt_attempts": n,
            "favorable_terminal_bunts": successes,
            "raw_terminal_success_rate": successes / n if n else np.nan,
            "shrunk_terminal_success_rate": float(posterior),
            "shrinkage_weight_player": float(n / (n + shrinkage)) if n + shrinkage > 0 else 0.0,
        }

    return BuntModel(
        definition=definition.upper(),
        rows=rows,
        terminal_distributions=terminal_distributions,
        global_terminal_distribution=global_terminal_distribution,
        branch_rates=branch_rates,
        global_abandon_rate=global_abandon_rate,
        player_effects=effects,
        league_success_rate=league_success_rate,
        shrinkage_prior_strength=float(shrinkage),
        abandonment_distributions=abandonment_distributions,
        global_abandonment_distribution=global_abandonment_distribution,
        abandonment_strategy=abandonment_strategy,
        shrinkage_prior_alpha=float(shrinkage_info["alpha"]),
        shrinkage_prior_beta=float(shrinkage_info["beta"]),
        shrinkage_method=str(shrinkage_info["method"]),
    )


def _estimate_beta_binomial_prior_strength(attempts: np.ndarray, successes: np.ndarray, league_rate: float) -> float:
    valid = attempts > 0
    if valid.sum() < 3:
        return 25.0
    rates = successes[valid] / attempts[valid]
    observed_var = float(np.var(rates, ddof=1)) if len(rates) > 1 else 0.0
    binomial_noise = float(np.mean(np.maximum(league_rate * (1.0 - league_rate) / attempts[valid], 0.0)))
    between = max(observed_var - binomial_noise, 1e-4)
    prior = league_rate * (1.0 - league_rate) / between - 1.0
    return float(np.clip(prior, 5.0, 80.0))


def _estimate_beta_binomial_prior(
    attempts: np.ndarray,
    successes: np.ndarray,
    league_rate: float,
    method: str = "beta_binomial_mle_fixed_mean",
) -> dict[str, float | str]:
    if method == "legacy_mom_capped":
        prior = _estimate_beta_binomial_prior_strength(attempts, successes, league_rate)
        return {
            "method": method,
            "prior_strength": float(prior),
            "alpha": float(max(league_rate * prior, 1e-9)),
            "beta": float(max((1.0 - league_rate) * prior, 1e-9)),
        }
    if method != "beta_binomial_mle_fixed_mean":
        raise ValueError(f"unknown bunt shrinkage method: {method}")

    valid = attempts > 0
    n = attempts[valid].astype(float)
    k = successes[valid].astype(float)
    if len(n) < 2:
        prior = 1_000_000.0
        return {
            "method": "beta_binomial_mle_fixed_mean_effective_complete_pooling",
            "prior_strength": prior,
            "alpha": float(max(league_rate * prior, 1e-9)),
            "beta": float(max((1.0 - league_rate) * prior, 1e-9)),
        }

    mu = float(min(max(league_rate, 1e-6), 1.0 - 1e-6))

    def log_likelihood(log_strength: float) -> float:
        strength = float(np.exp(log_strength))
        alpha = max(mu * strength, 1e-12)
        beta = max((1.0 - mu) * strength, 1e-12)
        total = 0.0
        for attempts_i, successes_i in zip(n, k):
            failures_i = attempts_i - successes_i
            total += (
                lgamma(successes_i + alpha)
                + lgamma(failures_i + beta)
                - lgamma(attempts_i + alpha + beta)
                - lgamma(alpha)
                - lgamma(beta)
                + lgamma(alpha + beta)
            )
        return float(total)

    lower = log(1e-3)
    upper = log(1e9)
    grid = np.linspace(lower, upper, 121)
    values = np.array([log_likelihood(float(x)) for x in grid])
    best_index = int(np.argmax(values))
    if best_index == len(grid) - 1:
        prior = 1e9
        method_name = "beta_binomial_mle_fixed_mean_effective_complete_pooling"
    else:
        left = float(grid[max(0, best_index - 1)])
        right = float(grid[min(len(grid) - 1, best_index + 1)])
        golden = (np.sqrt(5.0) - 1.0) / 2.0
        x1 = right - golden * (right - left)
        x2 = left + golden * (right - left)
        f1 = log_likelihood(x1)
        f2 = log_likelihood(x2)
        for _ in range(80):
            if f1 < f2:
                left = x1
                x1 = x2
                f1 = f2
                x2 = left + golden * (right - left)
                f2 = log_likelihood(x2)
            else:
                right = x2
                x2 = x1
                f2 = f1
                x1 = right - golden * (right - left)
                f1 = log_likelihood(x1)
        prior = float(np.exp((left + right) / 2.0))
        method_name = method
    return {
        "method": method_name,
        "prior_strength": float(prior),
        "alpha": float(max(mu * prior, 1e-9)),
        "beta": float(max((1.0 - mu) * prior, 1e-9)),
    }


def _compact_transition_rows(group: pd.DataFrame) -> list[dict[str, object]]:
    cols = ["next_base_state", "next_outs", "runs", "reconciled_category"]
    compact = group.groupby(cols, dropna=False).size().reset_index(name="count")
    return compact.to_dict(orient="records")


def _reconstruct_bunt_transition(row: object, movement: pd.DataFrame | None) -> dict[str, object]:
    start = {
        "1B": _nullable_int(getattr(row, "start_on_1b", None)),
        "2B": _nullable_int(getattr(row, "start_on_2b", None)),
        "3B": _nullable_int(getattr(row, "start_on_3b", None)),
    }
    batter_id = _nullable_int(getattr(row, "batter", None))
    event = str(getattr(row, "event", "") or "")
    destinations: dict[int, str] = {runner: base for base, runner in start.items() if runner is not None}
    outs_added = 0
    runs = 0
    if movement is not None and not movement.empty:
        for m in movement.itertuples(index=False):
            runner = _nullable_int(getattr(m, "runner_id", None))
            if runner is None:
                continue
            is_out = str(getattr(m, "is_out", "")).lower() == "true" or getattr(m, "is_out", False) is True
            if is_out:
                destinations.pop(runner, None)
                outs_added += 1
                continue
            end = getattr(m, "end_base", None)
            if pd.isna(end) or end in {None, ""}:
                continue
            end = str(end)
            if end.lower() == "score":
                destinations.pop(runner, None)
                runs += 1
            elif end in {"1B", "2B", "3B"}:
                destinations[runner] = end

    batter_reaches = event in {"single", "double", "triple", "home_run", "walk", "hit_by_pitch", "field_error", "catcher_interf", "force_out", "fielders_choice", "fielders_choice_out"}
    batter_out = event in {"sac_bunt", "field_out", "strikeout", "strikeout_double_play", "double_play", "grounded_into_double_play"}
    if batter_id is not None:
        if event == "home_run":
            runs += 1 + sum(1 for runner in list(destinations) if runner in set(start.values()))
            destinations = {runner: base for runner, base in destinations.items() if runner not in set(start.values())}
        elif event == "triple":
            destinations[batter_id] = "3B"
        elif event == "double":
            destinations[batter_id] = "2B"
        elif batter_reaches:
            destinations[batter_id] = "1B"
        elif batter_out:
            outs_added += 1 if not (movement is not None and batter_id in set(pd.to_numeric(movement.get("runner_id", pd.Series(dtype=float)), errors="coerce").dropna().astype(int))) else 0

    outs = min(int(getattr(row, "start_outs", 0)) + max(int(outs_added), 0), 3)
    if outs >= 3:
        return {"next_base_state": "---", "next_outs": 3, "runs": int(max(runs, 0))}
    occupied = {base: None for base in ("1B", "2B", "3B")}
    for _runner, base in destinations.items():
        if base in occupied and occupied[base] is None:
            occupied[base] = True
    next_base = ("1" if occupied["1B"] else "-") + ("2" if occupied["2B"] else "-") + ("3" if occupied["3B"] else "-")
    return {"next_base_state": next_base, "next_outs": outs, "runs": int(max(runs, 0))}


def _nullable_int(value: object) -> int | None:
    if value is None or pd.isna(value) or value == "":
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def save_bunt_model(model: BuntModel, path: str | Path) -> None:
    import json
    payload = {
        "definition": model.definition,
        "terminal_distributions": {f"{k[0]}|{k[1]}": v for k, v in model.terminal_distributions.items()},
        "global_terminal_distribution": model.global_terminal_distribution,
        "abandonment_distributions": {f"{k[0]}|{k[1]}": v for k, v in (model.abandonment_distributions or {}).items()},
        "global_abandonment_distribution": model.global_abandonment_distribution or [],
        "abandonment_strategy": model.abandonment_strategy,
        "branch_rates": {f"{k[0]}|{k[1]}": v for k, v in model.branch_rates.items()},
        "global_abandon_rate": model.global_abandon_rate,
        "player_effects": {str(k): v for k, v in model.player_effects.items()},
        "league_success_rate": model.league_success_rate,
        "shrinkage_prior_strength": model.shrinkage_prior_strength,
        "shrinkage_prior_alpha": model.shrinkage_prior_alpha,
        "shrinkage_prior_beta": model.shrinkage_prior_beta,
        "shrinkage_method": model.shrinkage_method,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_bunt_model(path: str | Path) -> BuntModel:
    import json
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    def parse_key(value: str) -> tuple[str, int]:
        base, outs = value.split("|")
        return base, int(outs)
    return BuntModel(
        definition=str(payload["definition"]),
        rows=pd.DataFrame(),
        terminal_distributions={parse_key(k): v for k, v in payload["terminal_distributions"].items()},
        global_terminal_distribution=list(payload["global_terminal_distribution"]),
        branch_rates={parse_key(k): float(v) for k, v in payload["branch_rates"].items()},
        global_abandon_rate=float(payload["global_abandon_rate"]),
        player_effects={int(k): v for k, v in payload["player_effects"].items()},
        league_success_rate=float(payload["league_success_rate"]),
        shrinkage_prior_strength=float(payload["shrinkage_prior_strength"]),
        abandonment_distributions={parse_key(k): v for k, v in payload.get("abandonment_distributions", {}).items()},
        global_abandonment_distribution=list(payload.get("global_abandonment_distribution", [])),
        abandonment_strategy=str(payload.get("abandonment_strategy", "normal_pa")),
        shrinkage_prior_alpha=payload.get("shrinkage_prior_alpha"),
        shrinkage_prior_beta=payload.get("shrinkage_prior_beta"),
        shrinkage_method=str(payload.get("shrinkage_method", "legacy_mom_capped")),
    )


def _player_bunt_effect(bunt_model: BuntModel, hitter: HitterProfile) -> dict[str, float]:
    value = _profile_mlbam_id(hitter)
    if value is None:
        return {}
    try:
        return bunt_model.player_effects.get(int(float(value)), {})
    except (TypeError, ValueError):
        return {}


def build_transition_tables(
    hitter: HitterProfile,
    config: PlanEngineConfig,
    samples_per_state: int,
    seed: int,
) -> tuple[dict[tuple[str, int], list[tuple[float, str, tuple[str, int] | None]]], dict[tuple[str, int], list[tuple[float, str, tuple[str, int] | None]]]]:
    rng = np.random.default_rng(seed)
    steal_tables = {}
    normal_pa_tables = {}
    for key in ALL_STATE_KEYS:
        state = state_from_key(key, hitter)
        steal_counter: dict[tuple[str, tuple[str, int] | None], int] = {}
        pa_counter: dict[tuple[str, tuple[str, int] | None], int] = {}
        for _ in range(samples_per_state):
            steal_result = apply_pre_pa_steal(state, rng, config)
            terminal, next_key = result_to_transition(steal_result)
            steal_counter[(terminal, next_key)] = steal_counter.get((terminal, next_key), 0) + 1

            outcome = sample_plan_outcome(hitter, rng, config, state=state, on_deck=hitter, inning=7, score_diff=0.0)
            pa_result = apply_plan_plate_appearance(state, hitter, outcome, rng, config)
            terminal, next_key = result_to_transition(pa_result)
            pa_counter[(terminal, next_key)] = pa_counter.get((terminal, next_key), 0) + 1
        steal_tables[key] = normalize_counter(steal_counter)
        normal_pa_tables[key] = normalize_counter(pa_counter)
    return steal_tables, normal_pa_tables


def _row_distribution_to_transitions(rows: list[dict[str, object]]) -> list[tuple[float, str, tuple[str, int] | None]]:
    weighted: dict[tuple[str, tuple[str, int] | None], float] = {}
    for row in rows:
        runs = int(row.get("runs", 0))
        outs = int(row.get("next_outs", 3))
        next_base = str(row.get("next_base_state", "---"))
        if runs > 0:
            key = ("success", None)
        elif outs >= 3:
            key = ("failure", None)
        else:
            key = ("state", (next_base, outs))
        weighted[key] = weighted.get(key, 0.0) + float(row.get("count", 1.0))
    return normalize_counter(weighted)


def terminal_bunt_distribution(
    hitter: HitterProfile,
    state: tuple[str, int],
    bunt_model: BuntModel,
) -> list[tuple[float, str, tuple[str, int] | None]]:
    terminal_rows = bunt_model.terminal_distributions.get(state, bunt_model.global_terminal_distribution)
    effect = _player_bunt_effect(bunt_model, hitter)
    player_success = float(effect.get("shrunk_terminal_success_rate", bunt_model.league_success_rate))
    league_success = max(min(bunt_model.league_success_rate, 0.999), 0.001)
    weighted: dict[tuple[str, tuple[str, int] | None], float] = {}
    for row in terminal_rows:
        category = str(row.get("reconciled_category"))
        favorable = category in FAVORABLE_BUNT_CATEGORIES
        if favorable:
            multiplier = player_success / league_success
        else:
            multiplier = (1.0 - player_success) / (1.0 - league_success)
        probability_mass = float(row.get("count", 1.0)) * max(multiplier, 0.05)
        runs = int(row.get("runs", 0))
        outs = int(row.get("next_outs", 3))
        next_base = str(row.get("next_base_state", "---"))
        if runs > 0:
            key = ("success", None)
        elif outs >= 3:
            key = ("failure", None)
        else:
            key = ("state", (next_base, outs))
        weighted[key] = weighted.get(key, 0.0) + probability_mass
    return normalize_counter(weighted)


def abandonment_transition_distribution(
    state: tuple[str, int],
    bunt_model: BuntModel,
) -> list[tuple[float, str, tuple[str, int] | None]] | None:
    if bunt_model.abandonment_strategy != "empirical_abandonment":
        return None
    rows = (bunt_model.abandonment_distributions or {}).get(state)
    if not rows:
        rows = bunt_model.global_abandonment_distribution or []
    if not rows:
        return None
    return _row_distribution_to_transitions(rows)


def bunt_transition_distribution(
    hitter: HitterProfile,
    state: tuple[str, int],
    bunt_model: BuntModel,
    normal_pa_distribution: list[tuple[float, str, tuple[str, int] | None]],
) -> list[tuple[float, str, tuple[str, int] | None]]:
    abandon = bunt_model.branch_rates.get(state, bunt_model.global_abandon_rate)
    terminal_distribution = terminal_bunt_distribution(hitter, state, bunt_model)
    abandon_distribution = abandonment_transition_distribution(state, bunt_model) or normal_pa_distribution
    combined: dict[tuple[str, tuple[str, int] | None], float] = {}
    for probability, terminal, key in terminal_distribution:
        combined[(terminal, key)] = combined.get((terminal, key), 0.0) + (1.0 - abandon) * probability
    for probability, terminal, key in abandon_distribution:
        combined[(terminal, key)] = combined.get((terminal, key), 0.0) + abandon * probability
    return normalize_counter(combined)


def solve_one_run_mdp(
    hitter: HitterProfile,
    config: PlanEngineConfig,
    bunt_model: BuntModel | None,
    samples_per_state: int = 2_000,
    seed: int = 202511,
    disable_bunts: bool = False,
    tolerance: float = 1e-8,
    max_iterations: int = 10_000,
) -> MdpResult:
    steal_tables, normal_pa_tables = build_transition_tables(hitter, config, samples_per_state, seed)
    values = {key: 0.0 for key in ALL_STATE_KEYS}
    policy = {key: "normal_pa" for key in ALL_STATE_KEYS}
    decision_rows: list[dict[str, object]] = []
    converged = False
    iterations = 0
    last_action_values: dict[tuple[str, int], tuple[float, float | None]] = {}

    for iteration in range(1, max_iterations + 1):
        after_values = {}
        next_policy = {}
        action_values: dict[tuple[str, int], tuple[float, float | None]] = {}
        for key in ALL_STATE_KEYS:
            q_normal = expected_from_distribution(normal_pa_tables[key], values)
            q_bunt = None
            if not disable_bunts and bunt_model is not None and is_eligible_bunt_state(key):
                q_bunt = expected_from_distribution(bunt_transition_distribution(hitter, key, bunt_model, normal_pa_tables[key]), values)
            if q_bunt is not None and q_bunt > q_normal:
                after_values[key] = q_bunt
                next_policy[key] = "sacrifice_bunt_strategy"
            else:
                after_values[key] = q_normal
                next_policy[key] = "normal_pa"
            action_values[key] = (q_normal, q_bunt)
        new_values = {key: expected_from_distribution(steal_tables[key], after_values) for key in ALL_STATE_KEYS}
        delta = max(abs(new_values[key] - values[key]) for key in ALL_STATE_KEYS)
        values = new_values
        policy = next_policy
        last_action_values = action_values
        iterations = iteration
        if delta < tolerance:
            converged = True
            break

    for key in ELIGIBLE_BUNT_STATES:
        q_normal, q_bunt = last_action_values.get(key, (np.nan, np.nan))
        decision_rows.append(
            {
                "base_state": key[0],
                "outs": key[1],
                "q_normal": q_normal,
                "q_bunt": q_bunt,
                "optimal_action": policy.get(key, "normal_pa"),
                "bunt_advantage_pp": (q_bunt - q_normal) * 100.0 if q_bunt is not None else np.nan,
            }
        )
    initial = ("---", 0)
    no_bunt_probability = values[initial] if disable_bunts else np.nan
    return MdpResult(
        player_id=_profile_mlbam_id(hitter),
        player_name=hitter.player_name,
        no_bunt_probability=float(no_bunt_probability),
        optimized_probability=float(values[initial]),
        iterations=iterations,
        converged=converged,
        policy=policy,
        decision_rows=decision_rows,
        values={key: float(value) for key, value in values.items()},
    )


def simulate_policy_one_run(
    hitter: HitterProfile,
    config: PlanEngineConfig,
    bunt_model: BuntModel,
    policy: Mapping[tuple[str, int], str],
    trials: int,
    seed: int,
    max_plate_appearances: int = 60,
) -> MonteCarloPolicyResult:
    rng = np.random.default_rng(seed)
    successes = 0
    bunt_attempts = 0
    reached = {f"{base}_{outs}": 0 for base, outs in ELIGIBLE_BUNT_STATES}
    for _ in range(trials):
        state = RunnerBaseState()
        pa = 0
        while state.outs < 3:
            if pa > max_plate_appearances:
                raise RuntimeError("policy one-run trial exceeded max plate appearances")
            steal = apply_pre_pa_steal(state, rng, config)
            if steal.runs > 0:
                successes += 1
                break
            state = steal.state
            if state.outs >= 3 and not steal.plate_appearance_completed:
                break
            key = state_key(state)
            if key in ELIGIBLE_BUNT_STATES:
                reached[f"{key[0]}_{key[1]}"] += 1
            if policy.get(key) == "sacrifice_bunt_strategy":
                bunt_attempts += 1
                result = sample_bunt_plate_appearance(state, hitter, bunt_model, rng, config)
            else:
                outcome = sample_plan_outcome(hitter, rng, config, state=state, on_deck=hitter, inning=7, score_diff=0.0)
                result = apply_plan_plate_appearance(state, hitter, outcome, rng, config)
            pa += 1
            if result.runs > 0:
                successes += 1
                break
            state = result.state
    probability = successes / trials
    se = float(np.sqrt(probability * (1.0 - probability) / trials))
    return MonteCarloPolicyResult(
        trials=trials,
        successes=successes,
        probability=float(probability),
        standard_error=se,
        ci95_low=float(max(0.0, probability - 1.96 * se)),
        ci95_high=float(min(1.0, probability + 1.96 * se)),
        bunt_attempts_per_trial=bunt_attempts / trials,
        reached_eligible_per_trial={key: value / trials for key, value in reached.items()},
    )


def sample_bunt_plate_appearance(
    state: RunnerBaseState,
    hitter: HitterProfile,
    bunt_model: BuntModel,
    rng: np.random.Generator,
    config: PlanEngineConfig,
) -> PlayResult:
    key = state_key(state)
    abandon = bunt_model.branch_rates.get(key, bunt_model.global_abandon_rate)
    if rng.random() < abandon:
        abandon_distribution = abandonment_transition_distribution(key, bunt_model)
        if abandon_distribution is not None:
            distribution = abandon_distribution
            probs = [row[0] for row in distribution]
            _prob, terminal, next_key = distribution[int(rng.choice(len(distribution), p=probs))]
            if terminal == "success":
                return PlayResult(RunnerBaseState(outs=state.outs), runs=1)
            if terminal == "failure" or next_key is None:
                return PlayResult(RunnerBaseState(outs=3), runs=0)
            return PlayResult(state_from_key(next_key, hitter), runs=0)
        outcome = sample_plan_outcome(hitter, rng, config, state=state, on_deck=hitter, inning=7, score_diff=0.0)
        return apply_plan_plate_appearance(state, hitter, outcome, rng, config)
    distribution = terminal_bunt_distribution(hitter, key, bunt_model)
    probs = [row[0] for row in distribution]
    chosen = distribution[int(rng.choice(len(distribution), p=probs))]
    _prob, terminal, next_key = chosen
    if terminal == "success":
        return PlayResult(RunnerBaseState(outs=state.outs), runs=1)
    if terminal == "failure" or next_key is None:
        return PlayResult(RunnerBaseState(outs=3), runs=0)
    return PlayResult(state_from_key(next_key, hitter), runs=0)
