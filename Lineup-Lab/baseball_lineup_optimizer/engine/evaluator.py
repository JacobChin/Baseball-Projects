"""Helpers for loading player pools and evaluating ordered lineups."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pandas as pd

from baseball_lineup_optimizer.engine.outcomes import HitterProfile
from baseball_lineup_optimizer.engine.simulation import SimulationResult, expected_runs

DEFAULT_STOLEN_BASE_RATES_PATH = Path("data/processed/contextual_stolen_base_rates_2025.csv")
CONTEXTUAL_STOLEN_BASE_RATE_COLUMNS = (
    "steal_2b_attempt_1xx_0",
    "steal_2b_attempt_1xx_1",
    "steal_2b_attempt_1xx_2",
    "steal_2b_attempt_1x3_0",
    "steal_2b_attempt_1x3_1",
    "steal_2b_attempt_1x3_2",
    "steal_3b_attempt_x2x_0",
    "steal_3b_attempt_x2x_1",
    "steal_3b_attempt_x2x_2",
    "steal_2b_success_1xx",
    "steal_2b_success_1x3",
    "steal_3b_success_x2x",
    "stolen_base_context",
)
LEGACY_STOLEN_BASE_RATE_COLUMNS = (
    "steal_2b_attempt_probability",
    "steal_2b_success_probability",
    "steal_3b_attempt_probability",
    "steal_3b_success_probability",
)
STOLEN_BASE_RATE_COLUMNS = (*CONTEXTUAL_STOLEN_BASE_RATE_COLUMNS, *LEGACY_STOLEN_BASE_RATE_COLUMNS)


def load_player_pool(path: str | Path) -> pd.DataFrame:
    """Load a processed Phase 2 player pool and attach revised stolen-base rates when available."""

    pool = pd.read_csv(path, encoding="utf-8")
    return attach_stolen_base_rates(pool)


def attach_stolen_base_rates(
    player_pool: pd.DataFrame,
    rates_path: str | Path = DEFAULT_STOLEN_BASE_RATES_PATH,
) -> pd.DataFrame:
    """Attach contextual 2B/3B steal attempt and success probabilities by MLBAM id."""

    path = Path(rates_path)
    if not path.exists() or "mlbam_id" not in player_pool.columns:
        return player_pool
    rates = pd.read_csv(path, encoding="utf-8")
    if "runner_id" not in rates.columns:
        return player_pool

    result = player_pool.drop(columns=[column for column in STOLEN_BASE_RATE_COLUMNS if column in player_pool.columns]).copy()
    result["mlbam_id"] = pd.to_numeric(result["mlbam_id"], errors="coerce").astype("Int64")

    contextual_columns = [column for column in STOLEN_BASE_RATE_COLUMNS if column in rates.columns]
    if contextual_columns:
        wide = rates[["runner_id", *contextual_columns]].rename(columns={"runner_id": "mlbam_id"}).copy()
        wide["mlbam_id"] = pd.to_numeric(wide["mlbam_id"], errors="coerce").astype("Int64")
        return result.merge(wide, on="mlbam_id", how="left")

    required = {"runner_id", "target_base", "standardized_attempt_probability_per_pa", "standardized_success_probability"}
    if not required.issubset(rates.columns):
        return result
    slim = rates[list(required)].copy()
    slim["target_base"] = slim["target_base"].astype(str).str.upper()
    wide_parts = []
    for target, prefix in (("2B", "steal_2b"), ("3B", "steal_3b")):
        part = slim[slim["target_base"].eq(target)][
            ["runner_id", "standardized_attempt_probability_per_pa", "standardized_success_probability"]
        ].rename(
            columns={
                "runner_id": "mlbam_id",
                "standardized_attempt_probability_per_pa": f"{prefix}_attempt_probability",
                "standardized_success_probability": f"{prefix}_success_probability",
            }
        )
        wide_parts.append(part)
    wide = wide_parts[0].merge(wide_parts[1], on="mlbam_id", how="outer")
    wide["mlbam_id"] = pd.to_numeric(wide["mlbam_id"], errors="coerce").astype("Int64")
    return result.merge(wide, on="mlbam_id", how="left")


def profiles_from_rows(rows: pd.DataFrame) -> list[HitterProfile]:
    """Convert player-pool rows to hitter profiles."""

    return [HitterProfile.from_mapping(row) for row in rows.to_dict(orient="records")]


def top_lineup_by_metric(
    player_pool: pd.DataFrame,
    metric: str,
    n: int = 9,
    ascending: bool = False,
) -> list[HitterProfile]:
    """Return the top `n` hitters by a player-pool metric in sorted order."""

    if metric not in player_pool.columns:
        raise ValueError(f"Metric not found in player pool: {metric}")
    rows = player_pool.sort_values(metric, ascending=ascending).head(n)
    return profiles_from_rows(rows)


def evaluate_lineup(
    lineup: Sequence[HitterProfile],
    games: int = 10_000,
    seed: int | None = 202503,
) -> SimulationResult:
    """Evaluate an ordered lineup with the Phase 3 MVP engine."""

    return expected_runs(lineup, games=games, seed=seed)

