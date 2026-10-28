"""Build hitter outcome probabilities from player-season event counts."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


EVENT_COUNT_COLUMNS = [
    "bb",
    "hbp",
    "single",
    "double",
    "triple",
    "hr",
    "k",
    "other_out",
]


@dataclass(frozen=True)
class ProbabilityCheck:
    """Summary of probability-integrity checks."""

    rows_checked: int
    max_probability_sum_error: float
    rows_with_negative_probabilities: int
    rows_with_missing_probabilities: int

    @property
    def passed(self) -> bool:
        return (
            self.max_probability_sum_error <= 1e-9
            and self.rows_with_negative_probabilities == 0
            and self.rows_with_missing_probabilities == 0
        )


def add_other_outs(df: pd.DataFrame) -> pd.DataFrame:
    """Compute other outs as PA minus known outcomes."""

    required = {"pa", "bb", "hbp", "single", "double", "triple", "hr", "k"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns needed to compute other_out: {sorted(missing)}")

    result = df.copy()
    known = result[["bb", "hbp", "single", "double", "triple", "hr", "k"]].sum(axis=1)
    result["other_out"] = result["pa"] - known
    return result


def add_outcome_probabilities(df: pd.DataFrame) -> pd.DataFrame:
    """Add per-PA outcome probabilities for the standard Phase 2 event set."""

    required = {"pa", *EVENT_COUNT_COLUMNS}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns needed for probabilities: {sorted(missing)}")

    result = df.copy()
    if (result["pa"] <= 0).any():
        raise ValueError("All rows must have positive PA.")

    for column in EVENT_COUNT_COLUMNS:
        result[f"p_{column}"] = result[column] / result["pa"]

    return result


def check_outcome_probabilities(df: pd.DataFrame) -> ProbabilityCheck:
    """Check that standard outcome probabilities are complete and sum to one."""

    probability_columns = [f"p_{column}" for column in EVENT_COUNT_COLUMNS]
    missing = set(probability_columns).difference(df.columns)
    if missing:
        raise ValueError(f"Missing probability columns: {sorted(missing)}")

    probabilities = df[probability_columns]
    sums = probabilities.sum(axis=1)
    return ProbabilityCheck(
        rows_checked=len(df),
        max_probability_sum_error=float((sums - 1.0).abs().max()) if len(df) else 0.0,
        rows_with_negative_probabilities=int((probabilities < 0).any(axis=1).sum()),
        rows_with_missing_probabilities=int(probabilities.isna().any(axis=1).sum()),
    )

