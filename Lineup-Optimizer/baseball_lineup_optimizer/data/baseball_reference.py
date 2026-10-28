"""Import hitter seasons from Baseball-Reference player pages."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import re

import pandas as pd
import requests


BASEBALL_REFERENCE_TABLES = {
    "players_standard_batting": {
        "year_id": "Season",
        "team_name_abbr": "Team",
        "b_pa": "PA",
        "b_ab": "AB",
        "b_h": "H",
        "b_doubles": "2B",
        "b_triples": "3B",
        "b_hr": "HR",
        "b_bb": "BB",
        "b_hbp": "HBP",
        "b_so": "SO",
        "b_sb": "SB",
        "b_cs": "CS",
    },
    "players_value_batting": {
        "year_id": "Season",
        "team_name_abbr": "Team",
        "b_pa": "PA",
        "b_runs_double_plays": "Rdp",
    },
    "players_advanced_batting": {
        "year_id": "Season",
        "team_name_abbr": "Team",
        "b_pa": "PA",
        "b_ld_perc": "LD%",
        "b_gb_perc": "GB%",
        "b_fb_perc": "FB%",
        "b_extra_bases_taken_perc": "XBT%",
    },
}


class _BaseballReferenceTableParser(HTMLParser):
    """Extract selected Baseball-Reference tables without optional HTML libraries."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: dict[str, list[dict[str, str]]] = {table_id: [] for table_id in BASEBALL_REFERENCE_TABLES}
        self._table_id: str | None = None
        self._table_depth = 0
        self._row: dict[str, str] | None = None
        self._cell_stat: str | None = None
        self._cell_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table":
            if self._table_id is not None:
                self._table_depth += 1
            elif attributes.get("id") in BASEBALL_REFERENCE_TABLES:
                self._table_id = str(attributes["id"])
                self._table_depth = 1
            return
        if self._table_id is None:
            return
        if tag == "tr":
            self._row = {}
        elif tag in {"th", "td"} and self._row is not None:
            self._cell_stat = attributes.get("data-stat")
            self._cell_text = []

    def handle_data(self, data: str) -> None:
        if self._cell_stat is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._table_id is None:
            return
        if tag in {"th", "td"} and self._row is not None and self._cell_stat is not None:
            value = re.sub(r"\s+", " ", "".join(self._cell_text)).strip()
            self._row[self._cell_stat] = value
            self._cell_stat = None
            self._cell_text = []
        elif tag == "tr" and self._row is not None:
            if self._row.get("year_id"):
                self.rows[self._table_id].append(self._row)
            self._row = None
        elif tag == "table":
            self._table_depth -= 1
            if self._table_depth <= 0:
                self._table_id = None
                self._table_depth = 0


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

    response = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LineupOptimizer/1.0)"},
    )
    if hasattr(response, "raise_for_status"):
        response.raise_for_status()
    html = response.text
    player_name = _player_name_from_html(html, url)
    parsed_tables = _parse_baseball_reference_tables(html)
    standard = parsed_tables["players_standard_batting"]
    value = parsed_tables["players_value_batting"]
    advanced = parsed_tables.get("players_advanced_batting")

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


def _parse_baseball_reference_tables(html: str) -> dict[str, pd.DataFrame]:
    parser = _BaseballReferenceTableParser()
    parser.feed(html)
    tables: dict[str, pd.DataFrame] = {}
    for table_id, columns in BASEBALL_REFERENCE_TABLES.items():
        rows = parser.rows[table_id]
        if not rows:
            if table_id == "players_advanced_batting":
                continue
            raise ValueError(f"Could not find Baseball-Reference table: {table_id}")
        tables[table_id] = pd.DataFrame(
            [{output: row.get(source, "") for source, output in columns.items()} for row in rows]
        )
    return tables


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
    if pd.isna(value) or str(value).strip() == "":
        return 0
    return int(float(str(value).replace(",", "")))


def _float_value(row: pd.Series, column: str) -> float:
    value = row.get(column, 0.0)
    if pd.isna(value) or str(value).strip() == "":
        return 0.0
    return float(str(value).replace(",", "").replace("%", ""))


def _percent_value(row: pd.Series, column: str, default: float) -> float:
    if row.empty:
        return default
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
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
