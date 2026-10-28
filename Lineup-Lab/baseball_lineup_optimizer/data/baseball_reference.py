"""Import hitter seasons from Baseball-Reference player pages."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
import re

import requests

import pandas as pd


@dataclass(frozen=True)
class BaseballReferenceHitterSeason:
    """Custom-hitter input values imported from Baseball-Reference."""

    name: str
    season: int
    team: str
    pa: int
    ab: int
    single: int
    double: int
    triple: int
    hr: int
    bb: int
    hbp: int
    k: int
    sb: int
    cs: int
    rdp: float
    xbt_rate: float
    gb_rate: float
    fb_rate: float
    ld_rate: float

    def as_form_defaults(self) -> dict[str, object]:
        return {
            "name": self.name,
            "pa": self.pa,
            "ab": self.ab,
            "single": self.single,
            "double": self.double,
            "triple": self.triple,
            "hr": self.hr,
            "bb": self.bb,
            "hbp": self.hbp,
            "k": self.k,
            "sb": self.sb,
            "cs": self.cs,
            "rdp": self.rdp,
            "xbt_rate": self.xbt_rate,
            "gb_rate": self.gb_rate,
            "fb_rate": self.fb_rate,
            "ld_rate": self.ld_rate,
        }


def import_baseball_reference_hitter_season(url: str, season: int) -> BaseballReferenceHitterSeason:
    """Import one player-season from a Baseball-Reference player page URL."""

    if "baseball-reference.com" not in url:
        raise ValueError("Paste a Baseball-Reference player page URL.")

    html = requests.get(url, timeout=20).text
    player_name = _player_name_from_html(html, url)
    tables = [_flatten_columns(table) for table in pd.read_html(StringIO(html))]
    standard = _find_table(tables, {"Season", "PA", "AB", "H", "2B", "3B", "HR", "BB", "SO"})
    value = _find_table(tables, {"Season", "PA", "Rdp"})
    advanced = _find_table(tables, {"Season", "PA", "LD%", "GB%", "FB%"}, required=False)

    standard_row = _season_row(standard, season)
    value_row = _season_row(value, season)
    advanced_row = _season_row(advanced, season) if advanced is not None else pd.Series(dtype=object)

    hits = _int_value(standard_row, "H")
    doubles = _int_value(standard_row, "2B")
    triples = _int_value(standard_row, "3B")
    homers = _int_value(standard_row, "HR")
    singles = hits - doubles - triples - homers

    return BaseballReferenceHitterSeason(
        name=f"{player_name} {season}",
        season=season,
        team=str(standard_row.get("Team", "")),
        pa=_int_value(standard_row, "PA"),
        ab=_int_value(standard_row, "AB"),
        single=singles,
        double=doubles,
        triple=triples,
        hr=homers,
        bb=_int_value(standard_row, "BB"),
        hbp=_int_value(standard_row, "HBP"),
        k=_int_value(standard_row, "SO"),
        sb=_int_value(standard_row, "SB"),
        cs=_int_value(standard_row, "CS"),
        rdp=_float_value(value_row, "Rdp"),
        xbt_rate=_percent_value(advanced_row, "XBT%", default=0.41),
        gb_rate=_percent_value(advanced_row, "GB%", default=0.42),
        fb_rate=_percent_value(advanced_row, "FB%", default=0.38),
        ld_rate=_percent_value(advanced_row, "LD%", default=0.20),
    )


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = [
            next((str(part) for part in reversed(column) if not str(part).startswith("Unnamed")), str(column[-1]))
            for column in result.columns
        ]
    else:
        result.columns = [str(column) for column in result.columns]
    return result


def _find_table(
    tables: list[pd.DataFrame],
    required_columns: set[str],
    required: bool = True,
) -> pd.DataFrame | None:
    for table in tables:
        if required_columns.issubset(set(table.columns)):
            return table
    if required:
        raise ValueError(f"Could not find Baseball-Reference table with columns: {sorted(required_columns)}")
    return None


def _season_row(table: pd.DataFrame, season: int) -> pd.Series:
    seasons = table["Season"].astype(str).str.extract(r"(\d{4})", expand=False)
    rows = table.loc[seasons == str(season)].copy()
    if rows.empty:
        raise ValueError(f"Could not find season {season} on that player page.")

    if "Team" in rows.columns:
        total_rows = rows.loc[rows["Team"].astype(str).isin({"2TM", "3TM"})]
        if not total_rows.empty:
            return total_rows.iloc[0]
    return rows.iloc[0]


def _int_value(row: pd.Series, column: str) -> int:
    value = row.get(column, 0)
    if pd.isna(value):
        return 0
    return int(float(str(value).replace(",", "")))


def _float_value(row: pd.Series, column: str) -> float:
    value = row.get(column, 0.0)
    if pd.isna(value):
        return 0.0
    return float(str(value).replace(",", "").replace("%", ""))


def _percent_value(row: pd.Series, column: str, default: float) -> float:
    if row.empty:
        return default
    value = row.get(column)
    if pd.isna(value):
        return default
    numeric = _float_value(row, column)
    return numeric / 100.0 if abs(numeric) > 1 else numeric


def _player_name_from_url(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1].replace(".shtml", "")
    return f"Imported {slug}"


def _player_name_from_html(html: str, url: str) -> str:
    match = re.search(r"<title>(.*?) Stats.*?</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return _player_name_from_url(url)
    return re.sub(r"\s+", " ", match.group(1)).strip()
