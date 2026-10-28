"""Hitter outcome profiles used by run-scoring engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np


OUTCOMES = ("bb", "hbp", "single", "double", "triple", "hr", "k", "other_out")


@dataclass(frozen=True)
class HitterProfile:
    """A player-season represented by per-PA event probabilities."""

    player_id: str
    player_name: str
    probabilities: dict[str, float]
    metadata: dict[str, object]

    @classmethod
    def from_mapping(cls, row: Mapping[str, object]) -> "HitterProfile":
        """Build a hitter profile from a player-pool row."""

        probabilities = {outcome: float(row[f"p_{outcome}"]) for outcome in OUTCOMES}
        total = sum(probabilities.values())
        if not np.isclose(total, 1.0):
            raise ValueError(f"Outcome probabilities must sum to one, got {total}")
        if any(value < 0 for value in probabilities.values()):
            raise ValueError("Outcome probabilities must be non-negative.")

        player_id = str(row.get("player_id", row.get("player_name", "")))
        player_name = str(row.get("player_name", player_id))
        metadata = {
            key: value
            for key, value in row.items()
            if key not in {f"p_{outcome}" for outcome in OUTCOMES}
        }
        return cls(
            player_id=player_id,
            player_name=player_name,
            probabilities=probabilities,
            metadata=metadata,
        )

    def sample_outcome(self, rng: np.random.Generator) -> str:
        """Sample one plate appearance outcome."""

        return str(rng.choice(OUTCOMES, p=[self.probabilities[outcome] for outcome in OUTCOMES]))


def make_synthetic_hitter(
    player_name: str,
    probabilities: Mapping[str, float],
    player_id: str | None = None,
) -> HitterProfile:
    """Create a synthetic hitter profile for validation examples."""

    complete = {outcome: float(probabilities.get(outcome, 0.0)) for outcome in OUTCOMES}
    total = sum(complete.values())
    if not np.isclose(total, 1.0):
        raise ValueError(f"Synthetic hitter probabilities must sum to one, got {total}")
    return HitterProfile(
        player_id=player_id or player_name,
        player_name=player_name,
        probabilities=complete,
        metadata={},
    )

