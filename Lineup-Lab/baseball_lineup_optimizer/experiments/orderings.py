"""Batting-order construction helpers for baseline experiments."""

from __future__ import annotations

import random
from collections.abc import Sequence

from baseball_lineup_optimizer.engine.outcomes import HitterProfile


def order_by_metric(
    lineup: Sequence[HitterProfile],
    metric: str,
    descending: bool = True,
) -> list[HitterProfile]:
    """Order hitters by a metadata metric."""

    return sorted(
        lineup,
        key=lambda hitter: _metric_value(hitter, metric),
        reverse=descending,
    )


def alternate_high_low(
    lineup: Sequence[HitterProfile],
    metric: str = "woba",
) -> list[HitterProfile]:
    """Alternate top and bottom hitters by a metric."""

    sorted_lineup = order_by_metric(lineup, metric, descending=True)
    ordered: list[HitterProfile] = []
    left = 0
    right = len(sorted_lineup) - 1
    while left <= right:
        ordered.append(sorted_lineup[left])
        left += 1
        if left <= right:
            ordered.append(sorted_lineup[right])
            right -= 1
    return ordered


def rotate_lineup(lineup: Sequence[HitterProfile], spots: int) -> list[HitterProfile]:
    """Rotate an ordered lineup left by `spots` positions."""

    if not lineup:
        return []
    offset = spots % len(lineup)
    return list(lineup[offset:]) + list(lineup[:offset])


def sabermetric_heuristic_order(lineup: Sequence[HitterProfile]) -> list[HitterProfile]:
    """A simple baseline order inspired by common sabermetric lineup advice.

    This is not an optimizer. It creates one plausible comparison order:
    strong OBP at 1/2, strongest overall bat at 4, power around 3/5,
    then remaining hitters by overall offensive quality.
    """

    remaining = list(lineup)

    def take_best(metric: str, descending: bool = True) -> HitterProfile:
        chosen = sorted(remaining, key=lambda h: _metric_value(h, metric), reverse=descending)[0]
        remaining.remove(chosen)
        return chosen

    first = take_best("obp")
    second = take_best("woba")
    fourth = take_best("woba")
    third = take_best("slg")
    fifth = take_best("slg")
    tail = order_by_metric(remaining, "woba", descending=True)
    return [first, second, third, fourth, fifth, *tail]


def random_orders(
    lineup: Sequence[HitterProfile],
    n: int,
    seed: int,
) -> list[list[HitterProfile]]:
    """Generate seeded random batting orders for a fixed hitter set."""

    rng = random.Random(seed)
    orders = []
    for _ in range(n):
        shuffled = list(lineup)
        rng.shuffle(shuffled)
        orders.append(shuffled)
    return orders


def lineup_names(lineup: Sequence[HitterProfile]) -> str:
    """Return a compact display string for a lineup."""

    return " / ".join(hitter.player_name for hitter in lineup)


def _metric_value(hitter: HitterProfile, metric: str) -> float:
    value = hitter.metadata.get(metric)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")

