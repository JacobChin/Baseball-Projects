"""Deterministic baserunner advancement rules for the Phase 3 MVP."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseOutState:
    """Base/out state before or after a plate appearance."""

    on_first: bool = False
    on_second: bool = False
    on_third: bool = False
    outs: int = 0

    @property
    def bases(self) -> tuple[bool, bool, bool]:
        return (self.on_first, self.on_second, self.on_third)


@dataclass(frozen=True)
class AdvancementResult:
    """Result of applying one event to a base/out state."""

    state: BaseOutState
    runs: int


def apply_deterministic_advancement(state: BaseOutState, outcome: str) -> AdvancementResult:
    """Apply simple deterministic advancement rules.

    MVP assumptions:
    - BB/HBP force runners only.
    - 1B advances every runner one base.
    - 2B advances every runner two bases.
    - 3B scores all runners.
    - HR scores all runners and the batter.
    - K and other_out add one out and runners hold.
    """

    if outcome in {"bb", "hbp"}:
        return _advance_walk_or_hbp(state)
    if outcome == "single":
        return AdvancementResult(
            BaseOutState(True, state.on_first, state.on_second, state.outs),
            runs=int(state.on_third),
        )
    if outcome == "double":
        return AdvancementResult(
            BaseOutState(False, True, state.on_first, state.outs),
            runs=int(state.on_second) + int(state.on_third),
        )
    if outcome == "triple":
        return AdvancementResult(
            BaseOutState(False, False, True, state.outs),
            runs=sum(state.bases),
        )
    if outcome == "hr":
        return AdvancementResult(
            BaseOutState(False, False, False, state.outs),
            runs=sum(state.bases) + 1,
        )
    if outcome in {"k", "other_out"}:
        return AdvancementResult(
            BaseOutState(state.on_first, state.on_second, state.on_third, state.outs + 1),
            runs=0,
        )
    raise ValueError(f"Unsupported outcome: {outcome}")


def empty_state() -> BaseOutState:
    """Return the start-of-inning base/out state."""

    return BaseOutState()


def _advance_walk_or_hbp(state: BaseOutState) -> AdvancementResult:
    force_third_home = state.on_first and state.on_second and state.on_third
    new_third = (state.on_second and state.on_first) or (state.on_third and not force_third_home)
    new_second = state.on_first
    return AdvancementResult(
        BaseOutState(True, new_second, new_third, state.outs),
        runs=int(force_third_home),
    )

