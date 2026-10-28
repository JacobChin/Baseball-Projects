"""Lineup-order optimization helpers for interactive use."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from baseball_lineup_optimizer.engine.outcomes import HitterProfile
from baseball_lineup_optimizer.engine.plan_engine import PlanEngineConfig, expected_runs_plan
from baseball_lineup_optimizer.engine.simulation import SimulationResult
from baseball_lineup_optimizer.experiments.orderings import (
    alternate_high_low,
    order_by_metric,
    random_orders,
    rotate_lineup,
    sabermetric_heuristic_order,
)


DEFAULT_ORDER_METRICS = (
    "woba",
    "wrc_plus",
    "obp",
    "slg",
    "iso",
    "bb_rate",
    "bb_per_k",
    "xbh_per_ab",
    "hr_per_ab",
    "single_per_ab",
    "bsr",
)


@dataclass(frozen=True)
class OptimizedLineup:
    """Best batting order found by the candidate-order optimizer."""

    lineup: list[HitterProfile]
    result: SimulationResult
    label: str
    orders_tested: int


def candidate_orders(
    lineup: Sequence[HitterProfile],
    random_order_count: int = 50,
    seed: int = 202503,
) -> list[tuple[str, list[HitterProfile]]]:
    """Create plausible orders to evaluate for a fixed set of nine hitters.

    This is a practical app optimizer rather than a full 9! exhaustive search.
    It tests common metric sorts, heuristic orders, rotations, high-low blends,
    and seeded random orders.
    """

    _validate_lineup(lineup)
    orders: list[tuple[str, list[HitterProfile]]] = [("Selected order", list(lineup))]

    for metric in DEFAULT_ORDER_METRICS:
        orders.append((f"{metric} descending", order_by_metric(lineup, metric, descending=True)))
        orders.append((f"{metric} ascending", order_by_metric(lineup, metric, descending=False)))
        orders.append((f"{metric} high-low", alternate_high_low(lineup, metric)))

    heuristic_order = sabermetric_heuristic_order(lineup)
    orders.append(("Sabermetric heuristic", heuristic_order))

    for spots in range(1, 9):
        orders.append((f"Selected order rotated {spots}", rotate_lineup(lineup, spots)))
        orders.append((f"Sabermetric heuristic rotated {spots}", rotate_lineup(heuristic_order, spots)))

    for index, order in enumerate(random_orders(lineup, random_order_count, seed=seed), start=1):
        orders.append((f"Random order {index}", order))

    return _dedupe_orders(orders)


def optimize_lineup_order(
    lineup: Sequence[HitterProfile],
    games_per_order: int = 250,
    final_games: int = 2_000,
    random_order_count: int = 50,
    seed: int = 202503,
    innings_per_game: int = 9,
    config: PlanEngineConfig | None = None,
) -> OptimizedLineup:
    """Find the best order among generated candidates for nine fixed hitters."""

    _validate_lineup(lineup)
    model_config = config or PlanEngineConfig()
    orders = candidate_orders(lineup, random_order_count=random_order_count, seed=seed)
    best_label = ""
    best_lineup: list[HitterProfile] | None = None
    best_result: SimulationResult | None = None

    for index, (label, order) in enumerate(orders):
        result = expected_runs_plan(
            order,
            games=games_per_order,
            seed=seed + index,
            innings_per_game=innings_per_game,
            config=model_config,
        )
        if best_result is None or result.runs_per_game > best_result.runs_per_game:
            best_label = label
            best_lineup = order
            best_result = result

    if best_lineup is None:
        raise RuntimeError("No lineup orders were evaluated.")

    final_result = expected_runs_plan(
        best_lineup,
        games=final_games,
        seed=seed + 100_000,
        innings_per_game=innings_per_game,
        config=model_config,
    )
    return OptimizedLineup(
        lineup=best_lineup,
        result=final_result,
        label=best_label,
        orders_tested=len(orders),
    )


def _dedupe_orders(orders: Sequence[tuple[str, list[HitterProfile]]]) -> list[tuple[str, list[HitterProfile]]]:
    seen: set[tuple[str, ...]] = set()
    deduped = []
    for label, order in orders:
        key = tuple(hitter.player_id for hitter in order)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((label, order))
    return deduped


def _validate_lineup(lineup: Sequence[HitterProfile]) -> None:
    if len(lineup) != 9:
        raise ValueError(f"Lineup must contain exactly 9 hitters, got {len(lineup)}.")
