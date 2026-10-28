"""Configuration loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class EligibilityConfig:
    """Rules for deciding which hitter-seasons enter the player pool."""

    season: int
    minimum_pa: int
    exclude_pitchers: bool = True
    combine_traded_players: bool = True


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file as a dictionary."""

    with Path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in YAML file: {path}")
    return data


def load_eligibility_config(path: str | Path) -> EligibilityConfig:
    """Load eligibility settings from a YAML file."""

    data = load_yaml(path)
    return EligibilityConfig(
        season=int(data["season"]),
        minimum_pa=int(data["minimum_pa"]),
        exclude_pitchers=bool(data.get("exclude_pitchers", True)),
        combine_traded_players=bool(data.get("combine_traded_players", True)),
    )

