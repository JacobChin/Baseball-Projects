"""Build a Phase 2 player-season pool from batting data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from pandas.api.types import is_numeric_dtype

from baseball_lineup_optimizer.config import EligibilityConfig
from baseball_lineup_optimizer.data.eligibility import apply_eligibility
from baseball_lineup_optimizer.features.hitter_outcomes import (
    EVENT_COUNT_COLUMNS,
    ProbabilityCheck,
    add_other_outs,
    add_outcome_probabilities,
    check_outcome_probabilities,
)


STANDARD_COLUMNS = [
    "player_id",
    "mlbam_id",
    "player_name",
    "season",
    "team",
    "primary_position",
    "pa",
    "ab",
    "bb",
    "ibb",
    "hbp",
    "sf",
    "sh",
    "single",
    "double",
    "triple",
    "hr",
    "xbh",
    "k",
    "other_out",
    "xbh_per_ab",
    "hr_per_ab",
    "single_per_ab",
    "bb_per_k",
    "gdp_per_pa",
    *[f"p_{column}" for column in EVENT_COUNT_COLUMNS],
    "woba",
    "wrc_plus",
    "obp",
    "slg",
    "iso",
    "bb_rate",
    "k_rate",
    "gb_rate",
    "fb_rate",
    "ld_rate",
    "popup_rate",
    "gb_count",
    "fb_count",
    "ld_count",
    "popup_count",
    "pull_rate",
    "center_rate",
    "oppo_rate",
    "sprint_speed",
    "home_to_first",
    "sb",
    "cs",
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
    "steal_2b_attempt_probability",
    "steal_2b_success_probability",
    "steal_3b_attempt_probability",
    "steal_3b_success_probability",
    "rdp",
    "gdp",
    "gdp_runs",
    "bsr",
    "war",
]


COLUMN_ALIASES = {
    "player_id": ["IDfg", "idfg", "playerid", "player_id"],
    "mlbam_id": ["xMLBAMID", "MLBAMID", "mlbam_id", "key_mlbam"],
    "player_name": ["PlayerName", "Name", "name", "Player", "player_name"],
    "season": ["Season", "season"],
    "team": ["TeamNameAbb", "TeamName", "Team", "team"],
    "primary_position": ["position", "positionDB", "primary_position", "Pos"],
    "pa": ["PA", "pa"],
    "ab": ["AB", "ab"],
    "bb": ["BB", "bb"],
    "ibb": ["IBB", "ibb"],
    "hbp": ["HBP", "hbp"],
    "sf": ["SF", "sf"],
    "sh": ["SH", "sh"],
    "single": ["1B", "1b", "single"],
    "double": ["2B", "2b", "double"],
    "triple": ["3B", "3b", "triple"],
    "hr": ["HR", "hr"],
    "k": ["SO", "K", "k"],
    "hits": ["H", "hits"],
    "woba": ["wOBA", "woba"],
    "wrc_plus": ["wRC+", "wrc_plus"],
    "obp": ["OBP", "obp"],
    "slg": ["SLG", "slg"],
    "iso": ["ISO", "iso"],
    "bb_rate": ["BB%", "BB%+", "bb_rate"],
    "k_rate": ["K%", "K%+", "k_rate"],
    "gb_rate": ["GB%", "gb_rate"],
    "fb_rate": ["FB%", "fb_rate"],
    "ld_rate": ["LD%", "ld_rate"],
    "popup_rate": ["IFFB%", "popup_rate"],
    "gb_count": ["GB", "gb_count"],
    "fb_count": ["FB", "fb_count"],
    "ld_count": ["LD", "ld_count"],
    "popup_count": ["IFFB", "popup_count"],
    "pull_rate": ["Pull%", "pull_rate"],
    "center_rate": ["Cent%", "Center%", "center_rate"],
    "oppo_rate": ["Oppo%", "oppo_rate"],
    "sprint_speed": ["Sprint Speed", "SprintSpeed", "sprint_speed"],
    "home_to_first": ["Home To First", "Home-to-First", "home_to_first", "HP to 1B"],
    "sb": ["SB", "sb"],
    "cs": ["CS", "cs"],
    "rdp": ["Rdp", "rdp"],
    "gdp": ["GDP", "GIDP", "gdp"],
    "gdp_runs": ["GDPRuns", "wGDP", "gdp_runs"],
    "bsr": ["BsR", "BaseRunning", "bsr"],
    "war": ["WAR", "war"],
}


@dataclass(frozen=True)
class PlayerPoolReport:
    """Summary of a built player pool."""

    season: int
    minimum_pa: int
    raw_rows: int
    eligible_rows: int
    probability_check: ProbabilityCheck
    negative_other_out_rows: int
    missing_required_rows: int

    @property
    def passed(self) -> bool:
        return (
            self.probability_check.passed
            and self.negative_other_out_rows == 0
            and self.missing_required_rows == 0
        )


def build_player_pool(raw_df: pd.DataFrame, config: EligibilityConfig) -> tuple[pd.DataFrame, PlayerPoolReport]:
    """Normalize raw batting data, apply eligibility, and add probabilities."""

    normalized = normalize_batting_table(raw_df, config.season)
    normalized = add_other_outs(normalized)
    normalized = add_rate_grouping_metrics(normalized)
    negative_other_out_rows = int((normalized["other_out"] < 0).sum())
    eligible = apply_eligibility(normalized, config)
    eligible = add_outcome_probabilities(eligible)
    probability_check = check_outcome_probabilities(eligible)

    required_for_model = ["pa", *EVENT_COUNT_COLUMNS]
    missing_required_rows = int(eligible[required_for_model].isna().any(axis=1).sum())

    output_columns = [column for column in STANDARD_COLUMNS if column in eligible.columns]
    sort_columns = [column for column in ["woba", "wrc_plus", "pa"] if column in eligible.columns]
    eligible = eligible[output_columns]
    if sort_columns:
        eligible = eligible.sort_values(
            by=sort_columns,
            ascending=[False] * len(sort_columns),
            na_position="last",
        )

    report = PlayerPoolReport(
        season=config.season,
        minimum_pa=config.minimum_pa,
        raw_rows=len(raw_df),
        eligible_rows=len(eligible),
        probability_check=probability_check,
        negative_other_out_rows=negative_other_out_rows,
        missing_required_rows=missing_required_rows,
    )
    return eligible.reset_index(drop=True), report


def normalize_batting_table(raw_df: pd.DataFrame, season: int) -> pd.DataFrame:
    """Normalize a FanGraphs-style batting table to project column names."""

    result = pd.DataFrame(index=raw_df.index)
    for standard_name, aliases in COLUMN_ALIASES.items():
        source = _first_present(raw_df.columns, aliases)
        if source is not None:
            result[standard_name] = raw_df[source]

    if "season" not in result.columns:
        result["season"] = season
    if "player_id" not in result.columns:
        result["player_id"] = result.get("player_name", pd.Series(index=raw_df.index, dtype="object"))
    if "team" not in result.columns:
        result["team"] = pd.NA
    if "primary_position" not in result.columns:
        result["primary_position"] = pd.NA

    for optional_count in ("ibb", "sf", "sh", "gb_count", "fb_count", "ld_count", "popup_count"):
        if optional_count not in result.columns:
            result[optional_count] = 0

    _derive_singles_if_needed(result)
    _coerce_numeric_columns(result, _numeric_columns(result.columns))

    required = ["player_name", "season", "pa", "bb", "hbp", "single", "double", "triple", "hr", "k"]
    missing = [column for column in required if column not in result.columns]
    if missing:
        raise ValueError(
            "The batting table cannot be converted to Phase 2 hitter outcomes. "
            f"Missing columns after normalization: {missing}"
        )

    return result


def add_rate_grouping_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add trait rates used to group scouting and optimizer candidates."""

    result = df.copy()
    if "ab" not in result.columns:
        result["ab"] = result["pa"] - result["bb"] - result["hbp"]
    result["xbh"] = result["double"] + result["triple"] + result["hr"]
    result["xbh_per_ab"] = _safe_divide(result["xbh"], result["ab"])
    result["hr_per_ab"] = _safe_divide(result["hr"], result["ab"])
    result["single_per_ab"] = _safe_divide(result["single"], result["ab"])
    result["bb_per_k"] = _safe_divide(result["bb"], result["k"])
    if "gdp" in result.columns:
        result["gdp_per_pa"] = _safe_divide(result["gdp"], result["pa"])
    return result


def write_player_pool_outputs(
    player_pool: pd.DataFrame,
    report: PlayerPoolReport,
    output_csv: str | Path,
    output_report: str | Path,
) -> None:
    """Write the Phase 2 player-pool CSV and markdown report."""

    csv_path = Path(output_csv)
    report_path = Path(output_report)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    player_pool.to_csv(csv_path, index=False)
    report_path.write_text(render_player_pool_report(player_pool, report, csv_path), encoding="utf-8")


def render_player_pool_report(player_pool: pd.DataFrame, report: PlayerPoolReport, csv_path: Path) -> str:
    """Render a compact markdown report for the Phase 2 checkpoint."""

    preview_columns = [
        "player_name",
        "team",
        "pa",
        "woba",
        "wrc_plus",
        "obp",
        "slg",
        "p_bb",
        "p_single",
        "p_double",
        "p_triple",
        "p_hr",
        "p_k",
        "p_other_out",
    ]
    preview_columns = [column for column in preview_columns if column in player_pool.columns]
    preview = player_pool.head(20)[preview_columns].to_markdown(index=False) if len(player_pool) else "_No eligible players._"

    return "\n".join(
        [
            "# Phase 2 Player Pool Checkpoint",
            "",
            f"- Season: {report.season}",
            f"- Minimum PA: {report.minimum_pa}",
            f"- Raw rows: {report.raw_rows}",
            f"- Eligible rows: {report.eligible_rows}",
            f"- Output CSV: `{csv_path}`",
            f"- Integrity passed: `{report.passed}`",
            "",
            "## Probability Checks",
            "",
            f"- Rows checked: {report.probability_check.rows_checked}",
            f"- Max probability sum error: {report.probability_check.max_probability_sum_error:.12f}",
            f"- Rows with negative probabilities: {report.probability_check.rows_with_negative_probabilities}",
            f"- Rows with missing probabilities: {report.probability_check.rows_with_missing_probabilities}",
            f"- Rows with negative computed other outs: {report.negative_other_out_rows}",
            f"- Rows missing required model counts: {report.missing_required_rows}",
            "",
            "## Top Preview",
            "",
            preview,
            "",
            "## Methodology Notes",
            "",
            "- `other_out` is computed as `PA - BB - HBP - 1B - 2B - 3B - HR - K`.",
            "- `XBH/AB`, `HR/AB`, `1B/AB`, and `BB/K` are derived for trait grouping and candidate scouting.",
            "- `GDP/PA` is derived for double-play tendency scouting and as a model fallback when GDP Runs is unavailable.",
            "- Descriptive fields such as wOBA, wRC+, OBP, SLG, ISO, batted-ball rates, SB, CS, Rdp, GDP, GDP runs, BsR, and WAR are retained for later analysis.",
            "- No baserunner advancement, run expectancy, batting-order, or optimization assumptions are introduced in this phase.",
            "",
        ]
    )


def _first_present(columns: Iterable[str], candidates: list[str]) -> str | None:
    column_set = set(columns)
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def _derive_singles_if_needed(df: pd.DataFrame) -> None:
    if "single" in df.columns:
        return
    if {"hits", "double", "triple", "hr"}.issubset(df.columns):
        df["single"] = df["hits"] - df["double"] - df["triple"] - df["hr"]


def _numeric_columns(columns: Iterable[str]) -> list[str]:
    non_numeric = {"player_id", "player_name", "team", "primary_position"}
    return [column for column in columns if column not in non_numeric]


def _coerce_numeric_columns(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column not in df.columns:
            continue
        values = df[column]
        if not is_numeric_dtype(values):
            values = values.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False)
        df[column] = pd.to_numeric(values, errors="coerce")
        if column.endswith("_rate"):
            df[column] = df[column].where(df[column].abs() <= 1, df[column] / 100.0)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return (numerator / denominator).where(denominator > 0, 0.0)
