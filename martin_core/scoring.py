"""Deterministic Martin Scoring Engine v2.0."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class MartinWeights:
    """Configurable weights for Martin Score calculation."""

    alpha: float = 0.60
    beta: float = 0.25
    gamma: float = 0.15
    delta: float = 0.50


DEFAULT_WEIGHTS = MartinWeights()


class MartinScoringEngine:
    """Computes deterministic Martin Score v2.0."""

    def __init__(self, weights: Optional[MartinWeights] = None) -> None:
        self.weights = weights if weights is not None else DEFAULT_WEIGHTS
        self.version = "martin-v2.0"

    def calculate_score(
        self,
        health: float,
        recovery_prob: float,
        confidence: float,
        risk: float,
    ) -> dict[str, Any]:
        """Calculates deterministic score clamped to [0.0, 100.0]."""
        s = max(0.0, min(100.0, health))
        p = max(0.0, min(100.0, recovery_prob))
        c = max(0.0, min(100.0, confidence))
        r = max(0.0, min(100.0, risk))
        score = max(
            0.0,
            min(
                100.0,
                round(
                    self.weights.alpha * s
                    + self.weights.beta * p
                    + self.weights.gamma * c
                    - self.weights.delta * r,
                    4,
                ),
            ),
        )
        return {"algorithm_version": self.version, "martin_score": score}
