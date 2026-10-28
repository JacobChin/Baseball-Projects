"""Sprint Speed attempt models for empirical joint transitions."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Mapping


DEFAULT_SPEED_ATTEMPT_MODEL_PATH = Path("data/processed/speed_attempt_models_2021_2025_direct_movement.json")
NEUTRAL_SPRINT_SPEED = 27.35


@dataclass(frozen=True)
class SpeedAttemptSpec:
    name: str
    event: str
    origin: str
    label: str
    attempt_destinations: frozenset[str]
    no_attempt_destinations: frozenset[str]
    coefficients: Mapping[str, float]
    model_type: str


@dataclass(frozen=True)
class SpeedAttemptAdjustment:
    model_name: str
    origin: str
    attempt_destinations: frozenset[str]
    no_attempt_destinations: frozenset[str]
    p_actual: float
    p_neutral: float


@dataclass
class SpeedAttemptStats:
    opportunities: dict[str, int] = field(default_factory=dict)
    neutral_fallbacks: dict[str, int] = field(default_factory=dict)

    def record_opportunity(self, model_name: str) -> None:
        self.opportunities[model_name] = self.opportunities.get(model_name, 0) + 1

    def record_neutral_fallback(self, model_name: str) -> None:
        self.neutral_fallbacks[model_name] = self.neutral_fallbacks.get(model_name, 0) + 1

    def total_opportunities(self) -> int:
        return sum(self.opportunities.values())


@dataclass(frozen=True)
class SpeedAttemptModel:
    season: int
    neutral_sprint_speed: float
    models: Mapping[str, SpeedAttemptSpec]
    validation: list[dict[str, object]]
    representative_probabilities: list[dict[str, object]]
    training_summary: list[dict[str, object]]

    @classmethod
    def from_json(cls, path: str | Path) -> "SpeedAttemptModel":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        models = {}
        for name, raw in dict(payload.get("models", {})).items():
            models[name] = SpeedAttemptSpec(
                name=name,
                event=str(raw["event"]),
                origin=str(raw["origin"]),
                label=str(raw.get("label", name)),
                attempt_destinations=frozenset(str(value) for value in raw["attempt_destinations"]),
                no_attempt_destinations=frozenset(str(value) for value in raw["no_attempt_destinations"]),
                coefficients={str(key): float(value) for key, value in dict(raw["coefficients"]).items()},
                model_type=str(raw.get("model_type", "linear")),
            )
        return cls(
            season=int(payload.get("season", 0)),
            neutral_sprint_speed=float(payload.get("neutral_sprint_speed", NEUTRAL_SPRINT_SPEED)),
            models=models,
            validation=list(payload.get("validation", [])),
            representative_probabilities=list(payload.get("representative_probabilities", [])),
            training_summary=list(payload.get("training_summary", [])),
        )

    def spec_for_context(self, event: str, origin: str, outs: int, detail: str | None) -> SpeedAttemptSpec | None:
        detail_text = str(detail or "")
        if event == "single" and detail_text not in {"lf", "cf", "rf"}:
            return None
        if event == "single" and origin == "first":
            return self.models.get("single_1b_to_3b")
        if event == "single" and origin == "second":
            return self.models.get("single_2b_to_home")
        if event == "double" and origin == "first":
            return self.models.get("double_1b_to_home")
        if event == "fb_out" and outs in {0, 1}:
            if origin == "first":
                return self.models.get("flyout_1b_to_2b")
            if origin == "second":
                return self.models.get("flyout_2b_to_3b")
            if origin == "third":
                return self.models.get("flyout_3b_to_home")
        return None

    def predict(self, model_name: str, sprint_speed: float, outs: int, detail: str | None) -> float | None:
        spec = self.models.get(model_name)
        if spec is None:
            return None
        z = 0.0
        features = speed_attempt_features(sprint_speed, self.neutral_sprint_speed, outs, detail, spec.model_type)
        for key, value in features.items():
            z += float(spec.coefficients.get(key, 0.0)) * value
        return _logistic(z)


@lru_cache(maxsize=4)
def load_speed_attempt_model(path: str | Path = DEFAULT_SPEED_ATTEMPT_MODEL_PATH) -> SpeedAttemptModel | None:
    model_path = Path(path)
    if not model_path.exists():
        return None
    return SpeedAttemptModel.from_json(model_path)


def speed_attempt_features(
    sprint_speed: float,
    neutral_sprint_speed: float,
    outs: int,
    detail: str | None,
    model_type: str,
) -> dict[str, float]:
    detail_text = str(detail or "unknown")
    features: dict[str, float] = {"intercept": 1.0, "speed_c": float(sprint_speed) - float(neutral_sprint_speed)}
    if model_type == "spline":
        centered = features["speed_c"]
        features["speed_c2"] = centered * centered
        features["speed_c3"] = centered * centered * centered
    features[f"outs_{int(outs)}"] = 1.0
    if detail_text in {"lf", "cf", "rf"}:
        features[f"detail_{detail_text}"] = 1.0
    elif detail_text:
        parts = detail_text.split("_", 1)
        if parts[0] in {"lf", "cf", "rf", "unknown"}:
            features[f"direction_{parts[0]}"] = 1.0
        if len(parts) > 1:
            features[f"distance_{parts[1]}"] = 1.0
    return features


def _logistic(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)
