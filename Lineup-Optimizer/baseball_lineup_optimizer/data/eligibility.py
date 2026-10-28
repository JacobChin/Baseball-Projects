"""Eligibility filtering for player-season batting data."""

from __future__ import annotations

import pandas as pd

from baseball_lineup_optimizer.config import EligibilityConfig


def apply_eligibility(df: pd.DataFrame, config: EligibilityConfig) -> pd.DataFrame:
    """Filter a player-season batting table to the configured hitter pool."""

    required = {"season", "pa"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required eligibility columns: {sorted(missing)}")

    eligible = df.loc[
        (df["season"].astype(int) == config.season)
        & (df["pa"].astype(float) >= config.minimum_pa)
    ].copy()

    if config.exclude_pitchers and "primary_position" in eligible.columns:
        eligible = eligible.loc[eligible["primary_position"].fillna("") != "P"].copy()

    return eligible.reset_index(drop=True)

