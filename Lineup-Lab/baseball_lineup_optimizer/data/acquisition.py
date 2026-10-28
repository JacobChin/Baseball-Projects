"""Data acquisition helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class DataAcquisitionError(RuntimeError):
    """Raised when a configured data source cannot be acquired."""


def fetch_fangraphs_pybaseball(season: int, minimum_pa: int = 0) -> pd.DataFrame:
    """Fetch FanGraphs batting stats through pybaseball."""

    try:
        from pybaseball import batting_stats
    except ImportError as exc:
        raise DataAcquisitionError(
            "pybaseball is not installed. Install the data extra with "
            "`python -m pip install -e \".[data]\"`."
        ) from exc

    try:
        return batting_stats(
            season,
            qual=minimum_pa,
            split_seasons=True,
            max_results=1_000_000,
        )
    except Exception as exc:  # pragma: no cover - depends on remote service behavior
        raise DataAcquisitionError(
            "FanGraphs acquisition through pybaseball failed. The current "
            "pybaseball FanGraphs route may be blocked by FanGraphs. Use a "
            "manually exported FanGraphs CSV with `--source-csv`."
        ) from exc


def read_fangraphs_csv(path: str | Path) -> pd.DataFrame:
    """Read a FanGraphs leaderboard CSV export."""

    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"FanGraphs CSV not found: {csv_path}")
    try:
        return pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(csv_path, encoding="utf-8-sig")
