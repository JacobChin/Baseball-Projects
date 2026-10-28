"""Context-adjusted non-intentional walk model for the plan simulator."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Mapping

import numpy as np


DEFAULT_CONTEXTUAL_WALK_MODEL_PATH = Path("data/processed/contextual_walk_model_2025.json")


@dataclass
class ContextualWalkModel:
    season: int
    intercept: float
    coefficients: dict[str, float]
    batter_effects: dict[str, float]
    re24_effects: dict[str, float]
    inning_effects: dict[str, float]
    threat_mean: float
    threat_scale: float
    score_mean: float
    score_scale: float
    pitcher_marginal_effect: float
    score_distributions: dict[str, list[tuple[float, float]]]
    threat_metric_by_batter: dict[str, float]
    default_threat_metric: float
    threat_spline_knots: list[float] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: str | Path) -> "ContextualWalkModel":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            season=int(payload["season"]),
            intercept=float(payload["intercept"]),
            coefficients={str(k): float(v) for k, v in payload.get("coefficients", {}).items()},
            batter_effects={str(k): float(v) for k, v in payload.get("batter_effects", {}).items()},
            re24_effects={str(k): float(v) for k, v in payload.get("re24_effects", {}).items()},
            inning_effects={str(k): float(v) for k, v in payload.get("inning_effects", {}).items()},
            threat_mean=float(payload.get("threat_mean", 0.0)),
            threat_scale=max(float(payload.get("threat_scale", 1.0)), 1e-9),
            score_mean=float(payload.get("score_mean", 0.0)),
            score_scale=max(float(payload.get("score_scale", 1.0)), 1e-9),
            pitcher_marginal_effect=float(payload.get("pitcher_marginal_effect", 0.0)),
            score_distributions={
                str(group): [(float(score), float(weight)) for score, weight in values]
                for group, values in payload.get("score_distributions", {}).items()
            },
            threat_metric_by_batter={str(k): float(v) for k, v in payload.get("threat_metric_by_batter", {}).items()},
            default_threat_metric=float(payload.get("default_threat_metric", 0.0)),
            threat_spline_knots=[float(value) for value in payload.get("threat_spline_knots", [])],
        )

    def predict_probability(
        self,
        batter_id: object,
        ondeck_id: object,
        base_state: str,
        outs: int,
        inning: int,
        score_diff: float | None = None,
    ) -> float:
        batter_key = _batter_key(batter_id)
        ondeck_key = _batter_key(ondeck_id)
        inning_group = _inning_group(inning)
        cache = getattr(self, "_prediction_cache", None)
        if cache is None:
            cache = {}
            self._prediction_cache = cache
        cache_key = (batter_key, ondeck_key, str(base_state), int(outs), inning_group, None if score_diff is None else float(score_diff))
        if cache_key in cache:
            return cache[cache_key]
        re24 = f"{int(outs)}|{base_state}"
        current_threat = self.threat_metric_by_batter.get(batter_key, self.default_threat_metric)
        ondeck_threat = self.threat_metric_by_batter.get(ondeck_key, self.default_threat_metric)
        threat_gap = current_threat - ondeck_threat
        threat_features = self._threat_features(threat_gap)
        first_base_open = 1.0 if not base_state.startswith("1") else 0.0

        base_logit = (
            self.intercept
            + self.pitcher_marginal_effect
            + self.batter_effects.get(batter_key, 0.0)
            + self.re24_effects.get(re24, 0.0)
            + self.inning_effects.get(inning_group, 0.0)
        )
        base_logit += self.coefficients.get("threat_linear", 0.0) * threat_features["linear"]
        base_logit += self.coefficients.get("threat_quadratic", 0.0) * threat_features["quadratic"]
        base_logit += self.coefficients.get("threat_cubic", 0.0) * threat_features["cubic"]
        base_logit += self.coefficients.get("threat_positive_hinge", 0.0) * threat_features["positive_hinge"]
        base_logit += self.coefficients.get("threat_negative_hinge", 0.0) * threat_features["negative_hinge"]
        for index, spline_value in enumerate(threat_features["spline"]):
            base_logit += self.coefficients.get(f"threat_spline_{index}", 0.0) * spline_value
        base_logit += first_base_open * (
            self.coefficients.get("fbo_threat_linear", 0.0) * threat_features["linear"]
            + self.coefficients.get("fbo_threat_quadratic", 0.0) * threat_features["quadratic"]
            + self.coefficients.get("fbo_threat_cubic", 0.0) * threat_features["cubic"]
            + self.coefficients.get("fbo_threat_positive_hinge", 0.0) * threat_features["positive_hinge"]
            + self.coefficients.get("fbo_threat_negative_hinge", 0.0) * threat_features["negative_hinge"]
            + sum(
                self.coefficients.get(f"fbo_threat_spline_{index}", 0.0) * spline_value
                for index, spline_value in enumerate(threat_features["spline"])
            )
        )
        base_logit += self.coefficients.get(f"re24_threat::{re24}", 0.0) * threat_features["linear"]

        distribution = [(float(score_diff), 1.0)] if score_diff is not None else (self.score_distributions.get(inning_group) or [(0.0, 1.0)])
        probability = 0.0
        for score_diff, weight in distribution:
            score_z = (score_diff - self.score_mean) / self.score_scale
            logit = (
                base_logit
                + self.coefficients.get("score_linear", 0.0) * score_z
                + self.coefficients.get("score_quadratic", 0.0) * (score_z**2)
                + self.coefficients.get(f"inning_score::{inning_group}", 0.0) * score_z
            )
            probability += weight * _sigmoid(logit)
        clipped = float(np.clip(probability, 0.0, 0.5))
        cache[cache_key] = clipped
        return clipped

    def _threat_features(self, threat_gap: float) -> dict[str, float]:
        z = (float(threat_gap) - self.threat_mean) / self.threat_scale
        return {
            "linear": z,
            "quadratic": z * z,
            "cubic": z * z * z,
            "positive_hinge": max(z - 0.5, 0.0),
            "negative_hinge": max(-z - 0.5, 0.0),
            "spline": [max(z - knot, 0.0) ** 3 for knot in self.threat_spline_knots],
        }


@lru_cache(maxsize=4)
def load_contextual_walk_model(path: str | Path = DEFAULT_CONTEXTUAL_WALK_MODEL_PATH) -> ContextualWalkModel | None:
    model_path = Path(path)
    if not model_path.exists():
        return None
    return ContextualWalkModel.from_json(model_path)


def _inning_group(inning: int) -> str:
    inning = int(inning)
    if inning <= 3:
        return "early"
    if inning <= 6:
        return "middle"
    return "late"


def _batter_key(value: object) -> str:
    try:
        if value is None or bool(getattr(value, "isna", lambda: False)()):
            return ""
    except TypeError:
        pass
    try:
        numeric = float(value)
        if np.isnan(numeric):
            return ""
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return str(value)


def _sigmoid(value: float) -> float:
    value = float(np.clip(value, -35.0, 35.0))
    return 1.0 / (1.0 + np.exp(-value))
