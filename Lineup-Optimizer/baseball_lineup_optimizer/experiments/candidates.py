"""Candidate-pool construction for optimizer experiments."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CandidateMetric:
    """Metric rule used to include hitters in the candidate pool."""

    name: str
    column: str
    ascending: bool = False


DEFAULT_CANDIDATE_METRICS = [
    CandidateMetric("high_woba", "woba"),
    CandidateMetric("high_wrc_plus", "wrc_plus"),
    CandidateMetric("high_obp", "obp"),
    CandidateMetric("high_slg", "slg"),
    CandidateMetric("high_iso", "iso"),
    CandidateMetric("high_bb_rate", "bb_rate"),
    CandidateMetric("low_k_rate", "k_rate", ascending=True),
    CandidateMetric("high_xbh_per_ab", "xbh_per_ab"),
    CandidateMetric("high_hr_per_ab", "hr_per_ab"),
    CandidateMetric("high_single_per_ab", "single_per_ab"),
    CandidateMetric("high_bb_per_k", "bb_per_k"),
]


def build_candidate_pool(
    player_pool: pd.DataFrame,
    top_k_per_metric: int = 30,
    metrics: list[CandidateMetric] | None = None,
) -> pd.DataFrame:
    """Return the union of top hitters under candidate-pool metric rules."""

    metrics = metrics or DEFAULT_CANDIDATE_METRICS
    selected_frames = []
    for metric in metrics:
        if metric.column not in player_pool.columns:
            raise ValueError(f"Candidate metric column not found: {metric.column}")
        frame = (
            player_pool.sort_values(metric.column, ascending=metric.ascending)
            .head(top_k_per_metric)
            .copy()
        )
        frame["candidate_reason"] = metric.name
        selected_frames.append(frame)

    selected = pd.concat(selected_frames, ignore_index=True)
    reason_by_player = (
        selected.groupby("player_id")["candidate_reason"]
        .apply(lambda values: ";".join(sorted(set(values))))
        .rename("candidate_reasons")
    )
    pool = (
        player_pool.loc[player_pool["player_id"].isin(reason_by_player.index)]
        .merge(reason_by_player, on="player_id")
        .sort_values("woba", ascending=False)
        .reset_index(drop=True)
    )
    return pool


def add_component_composite(player_pool: pd.DataFrame) -> pd.DataFrame:
    """Add a transparent component-score column for exploratory lineups."""

    result = player_pool.copy()
    score_columns = ["woba", "bb_per_k", "xbh_per_ab", "hr_per_ab", "single_per_ab"]
    penalty_columns = ["k_rate"]
    result["component_score"] = 0.0
    for column in score_columns:
        result["component_score"] += _zscore(result[column])
    for column in penalty_columns:
        result["component_score"] -= _zscore(result[column])
    return result


def _zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0:
        return series * 0.0
    return (series - series.mean()) / std
