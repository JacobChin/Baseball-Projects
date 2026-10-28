"""Monte Carlo lineup simulation for the Phase 3 MVP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from baseball_lineup_optimizer.engine.advancement import (
    BaseOutState,
    apply_deterministic_advancement,
    empty_state,
)
from baseball_lineup_optimizer.engine.outcomes import HitterProfile


@dataclass(frozen=True)
class SimulationResult:
    """Summary of a Monte Carlo lineup simulation."""

    runs_per_game: float
    games: int
    innings_per_game: int
    seed: int | None
    run_std: float
    run_min: int
    run_max: int


def simulate_game(
    lineup: Sequence[HitterProfile],
    rng: np.random.Generator,
    innings: int = 9,
    max_plate_appearances: int = 500,
) -> int:
    """Simulate one game-equivalent using a cyclic batting order."""

    _validate_lineup(lineup)
    runs = 0
    batter_index = 0
    plate_appearances = 0
    for _inning in range(innings):
        state = empty_state()
        while state.outs < 3:
            plate_appearances += 1
            if plate_appearances > max_plate_appearances:
                raise RuntimeError(
                    "Simulation exceeded max_plate_appearances. "
                    "This usually means the lineup has too little out probability."
                )
            hitter = lineup[batter_index % len(lineup)]
            batter_index += 1
            result = apply_deterministic_advancement(state, hitter.sample_outcome(rng))
            runs += result.runs
            state = result.state
    return runs


def expected_runs(
    lineup: Sequence[HitterProfile],
    games: int = 10_000,
    seed: int | None = 202503,
    innings_per_game: int = 9,
    max_plate_appearances_per_game: int = 500,
) -> SimulationResult:
    """Estimate expected runs per game for an ordered lineup."""

    _validate_lineup(lineup)
    if games <= 0:
        raise ValueError("games must be positive.")
    if innings_per_game <= 0:
        raise ValueError("innings_per_game must be positive.")

    rng = np.random.default_rng(seed)
    runs = np.array(
        [
            simulate_game(
                lineup,
                rng,
                innings=innings_per_game,
                max_plate_appearances=max_plate_appearances_per_game,
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


def _validate_lineup(lineup: Sequence[HitterProfile]) -> None:
    if len(lineup) != 9:
        raise ValueError(f"Lineup must contain exactly 9 hitters, got {len(lineup)}.")
