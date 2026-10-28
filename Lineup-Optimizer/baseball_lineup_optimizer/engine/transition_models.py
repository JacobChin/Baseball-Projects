
"""Empirical transition models for the plan-aligned lineup simulator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping

import numpy as np


DEFAULT_TRANSITION_MODEL_PATH = Path("data/processed/transition_models_2021_2025_direct_movement.json")


@dataclass(frozen=True)
class EmpiricalTransition:
    """A sampled whole-play transition learned from historical play outcomes."""

    batter: str
    first: str
    second: str
    third: str
    outs_added: int
    runs: int


@dataclass(frozen=True)
class TransitionModel:
    """Historical transition and secondary batted-ball distributions."""

    season: int
    transitions: dict[str, list[dict[str, object]]]
    hitter_distributions: dict[str, dict[str, dict[str, float]]]
    league_distributions: dict[str, dict[str, float]]
    min_exact_count: int = 25

    @classmethod
    def from_json(cls, path: str | Path) -> "TransitionModel":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            season=int(payload.get("season", 0)),
            transitions={key: _compact_rows(rows) for key, rows in dict(payload.get("transitions", {})).items()},
            hitter_distributions=dict(payload.get("hitter_distributions", {})),
            league_distributions=dict(payload.get("league_distributions", {})),
            min_exact_count=int(payload.get("min_exact_count", 25)),
        )

    def sample_transition(
        self,
        event: str,
        outs: int,
        base_state: str,
        detail: str | None,
        rng: np.random.Generator,
        origin_multipliers: Mapping[str, float] | None = None,
        attempt_adjustments: list[Mapping[str, object]] | None = None,
        double_play_multiplier: float = 1.0,
    ) -> EmpiricalTransition | None:
        """Sample the most specific available empirical transition.

        Optional multipliers tilt the historical joint-outcome distribution toward
        runner-specific advancement or batter-specific GDP tendencies while keeping
        sampled plays inside transitions that actually occurred in MLB data.
        """

        keys = [
            transition_key(event, outs, base_state, detail),
            transition_key(event, outs, base_state, None),
            transition_key(event, None, base_state, None),
            transition_key(event, None, None, None),
        ]
        for key in keys:
            rows = self.transitions.get(key, [])
            if not rows:
                continue
            if key == keys[0] and len(rows) < self.min_exact_count:
                continue
            sampled = _weighted_sample(rows, event, rng, origin_multipliers or {}, double_play_multiplier, attempt_adjustments or [])
            return EmpiricalTransition(
                batter=str(sampled.get("batter", "out")),
                first=str(sampled.get("first", "empty")),
                second=str(sampled.get("second", "empty")),
                third=str(sampled.get("third", "empty")),
                outs_added=int(sampled.get("outs_added", 1)),
                runs=int(sampled.get("runs", 0)),
            )
        return None

    def sample_detail(
        self,
        batter_id: object,
        distribution_name: str,
        rng: np.random.Generator,
    ) -> str:
        """Sample a player-specific secondary detail, falling back to league rates."""

        batter_key = _batter_key(batter_id)
        player = self.hitter_distributions.get(batter_key, {}).get(distribution_name, {})
        distribution = player or self.league_distributions.get(distribution_name, {})
        if not distribution:
            return "unknown"
        labels = list(distribution)
        probabilities = np.array([float(distribution[label]) for label in labels], dtype=float)
        total = probabilities.sum()
        if total <= 0:
            return "unknown"
        probabilities = probabilities / total
        return str(rng.choice(labels, p=probabilities))

    def model_summary(self) -> dict[str, object]:
        return {
            "season": self.season,
            "transition_keys": len(self.transitions),
            "transition_rows": int(sum(sum(int(row.get("count", 1)) for row in rows) for rows in self.transitions.values())),
            "unique_transition_rows": sum(len(rows) for rows in self.transitions.values()),
            "hitter_profiles": len(self.hitter_distributions),
            "league_distributions": sorted(self.league_distributions),
        }


@lru_cache(maxsize=4)
def load_transition_model(path: str | Path = DEFAULT_TRANSITION_MODEL_PATH) -> TransitionModel | None:
    model_path = Path(path)
    if not model_path.exists():
        return None
    return TransitionModel.from_json(model_path)


def transition_key(event: str, outs: int | None, base_state: str | None, detail: str | None) -> str:
    outs_part = "*" if outs is None else str(int(outs))
    base_part = "*" if base_state is None else str(base_state)
    detail_part = "*" if detail is None else str(detail)
    return f"{event}|{outs_part}|{base_part}|{detail_part}"


def base_state_from_occupancy(first: object | None, second: object | None, third: object | None) -> str:
    return "".join(["1" if first is not None else "-", "2" if second is not None else "-", "3" if third is not None else "-"])


def normalize_distribution(counts: Mapping[str, float]) -> dict[str, float]:
    clean = {str(key): max(float(value), 0.0) for key, value in counts.items()}
    total = sum(clean.values())
    if total <= 0:
        return {}
    return {key: value / total for key, value in clean.items()}


def shrink_categorical_counts(
    player_counts: Mapping[str, float],
    league_probabilities: Mapping[str, float],
    prior_strength: float,
) -> dict[str, float]:
    """Dirichlet-multinomial posterior mean for sparse player detail distributions."""

    labels = sorted(set(player_counts) | set(league_probabilities))
    player_total = sum(max(float(player_counts.get(label, 0.0)), 0.0) for label in labels)
    denominator = player_total + prior_strength
    if denominator <= 0:
        return normalize_distribution(league_probabilities)
    posterior = {
        label: (
            max(float(player_counts.get(label, 0.0)), 0.0)
            + prior_strength * max(float(league_probabilities.get(label, 0.0)), 0.0)
        )
        / denominator
        for label in labels
    }
    return normalize_distribution(posterior)


def _compact_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: dict[tuple[object, ...], int] = {}
    for row in rows:
        count = int(row.get("count", 1))
        key = (
            str(row.get("batter", "out")),
            str(row.get("first", "empty")),
            str(row.get("second", "empty")),
            str(row.get("third", "empty")),
            int(row.get("outs_added", 1)),
            int(row.get("runs", 0)),
        )
        counts[key] = counts.get(key, 0) + count
    return [
        {
            "batter": key[0],
            "first": key[1],
            "second": key[2],
            "third": key[3],
            "outs_added": key[4],
            "runs": key[5],
            "count": count,
        }
        for key, count in counts.items()
    ]


def _weighted_sample(
    rows: list[dict[str, object]],
    event: str,
    rng: np.random.Generator,
    origin_multipliers: Mapping[str, float],
    double_play_multiplier: float,
    attempt_adjustments: list[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    weights = np.array(
        [
            float(row.get("count", 1.0))
            * _transition_weight(row, event, origin_multipliers, double_play_multiplier, attempt_adjustments or [])
            for row in rows
        ],
        dtype=float,
    )
    total = weights.sum()
    if total <= 0 or not np.isfinite(total):
        return rows[int(rng.integers(0, len(rows)))]
    return rows[int(rng.choice(len(rows), p=weights / total))]


def _transition_weight(
    row: Mapping[str, object],
    event: str,
    origin_multipliers: Mapping[str, float],
    double_play_multiplier: float,
    attempt_adjustments: list[Mapping[str, object]] | None = None,
) -> float:
    weight = 1.0
    if event == "gb_out" and int(row.get("outs_added", 0)) >= 2:
        weight *= max(float(double_play_multiplier), 0.05)
    for origin, multiplier in origin_multipliers.items():
        destination = str(row.get(origin, "empty"))
        if destination in {"empty", "out"}:
            if destination == "out":
                weight *= 1.0 / max(float(multiplier), 0.10)
            continue
        if _is_extra_advancement(origin, destination):
            weight *= max(float(multiplier), 0.10)
    for adjustment in attempt_adjustments or []:
        weight *= _attempt_adjustment_weight(row, adjustment)
    return max(weight, 0.0)


def _attempt_adjustment_weight(row: Mapping[str, object], adjustment: Mapping[str, object]) -> float:
    origin = str(adjustment.get("origin", ""))
    destination = str(row.get(origin, "empty"))
    attempt_destinations = {str(value) for value in adjustment.get("attempt_destinations", [])}
    no_attempt_destinations = {str(value) for value in adjustment.get("no_attempt_destinations", [])}
    p_actual = float(adjustment.get("p_actual", 0.0))
    p_neutral = float(adjustment.get("p_neutral", 0.0))
    epsilon = 1e-6
    p_actual = float(np.clip(p_actual, epsilon, 1.0 - epsilon))
    p_neutral = float(np.clip(p_neutral, epsilon, 1.0 - epsilon))
    if destination in attempt_destinations:
        return p_actual / p_neutral
    if destination in no_attempt_destinations:
        return (1.0 - p_actual) / (1.0 - p_neutral)
    return 1.0





def _is_extra_advancement(origin: str, destination: str) -> bool:
    if destination == "score":
        return True
    return (origin, destination) in {
        ("first", "second"),
        ("first", "third"),
        ("first", "score"),
        ("second", "third"),
        ("second", "score"),
        ("third", "score"),
    }


def _batter_key(batter_id: object) -> str:
    try:
        if batter_id is None or bool(getattr(batter_id, "isna", lambda: False)()):
            return ""
    except TypeError:
        pass
    try:
        numeric = float(batter_id)
        if np.isnan(numeric):
            return ""
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return str(batter_id)
