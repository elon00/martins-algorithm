"""Deterministic Martin scoring utilities.

This module preserves the feature-based Candidate API used by the classifier,
optimizer and tests while also exposing the newer 0-100 scoring engine.
Scores are research heuristics, not investment recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Any, Mapping, Optional


DEFAULT_WEIGHTS: dict[str, float] = {
    "market_activity": 0.15,
    "liquidity": 0.15,
    "volume": 0.10,
    "onchain_activity": 0.10,
    "developer_activity": 0.10,
    "exchange_activity": 0.05,
    "project_health": 0.15,
    "recovery_evidence": 0.10,
    "ownership_evidence": 0.10,
}


@dataclass(frozen=True)
class Candidate:
    """Normalized research candidate consumed by the feature scoring pipeline."""

    asset_id: str
    features: Mapping[str, float]
    risk: float = 0.0
    confidence: float = 1.0


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    """Clamp a scalar to an inclusive interval."""
    return max(lower, min(upper, float(value)))


def sigmoid(value: float) -> float:
    """Numerically stable logistic transform."""
    if value >= 0:
        z = exp(-value)
        return 1.0 / (1.0 + z)
    z = exp(value)
    return z / (1.0 + z)


def martin_score(
    candidate: Candidate,
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    """Return a deterministic research score in the inclusive range 0 to 1.

    Missing features contribute zero. The score is a ranking heuristic only
    and does not establish ownership, recoverability, value, or investment
    return.
    """
    selected_weights = dict(weights or DEFAULT_WEIGHTS)
    weight_total = sum(
        max(0.0, float(weight)) for weight in selected_weights.values()
    )
    if weight_total <= 0:
        raise ValueError("scoring weights must contain a positive total weight")

    evidence = sum(
        clamp(float(candidate.features.get(name, 0.0)))
        * max(0.0, float(weight))
        for name, weight in selected_weights.items()
    ) / weight_total

    confidence = clamp(candidate.confidence)
    risk = clamp(candidate.risk)
    confidence_adjusted = evidence * (0.5 + 0.5 * confidence)
    return round(clamp(confidence_adjusted - 0.35 * risk), 12)


def rank_candidates(
    candidates: list[Candidate],
    top_k: int | None = None,
) -> list[tuple[Candidate, float]]:
    """Rank candidates by descending Martin score."""
    ranked = sorted(
        ((candidate, martin_score(candidate)) for candidate in candidates),
        key=lambda item: item[1],
        reverse=True,
    )
    if top_k is None:
        return ranked
    if top_k < 0:
        raise ValueError("top_k must be non-negative")
    return ranked[:top_k]


@dataclass(frozen=True)
class MartinWeights:
    """Weights for the separate 0-100 operational score helper."""

    alpha: float = 0.60
    beta: float = 0.25
    gamma: float = 0.15
    delta: float = 0.50


OPERATIONAL_DEFAULT_WEIGHTS = MartinWeights()


class MartinScoringEngine:
    """Compute a bounded 0-100 operational research score."""

    def __init__(self, weights: Optional[MartinWeights] = None) -> None:
        self.weights = (
            weights if weights is not None else OPERATIONAL_DEFAULT_WEIGHTS
        )
        self.version = "martin-v2.0"

    def calculate_score(
        self,
        health: float,
        recovery_prob: float,
        confidence: float,
        risk: float,
    ) -> dict[str, Any]:
        s = max(0.0, min(100.0, float(health)))
        p = max(0.0, min(100.0, float(recovery_prob)))
        conf = max(0.0, min(100.0, float(confidence)))
        r = max(0.0, min(100.0, float(risk)))
        score = max(
            0.0,
            min(
                100.0,
                round(
                    self.weights.alpha * s
                    + self.weights.beta * p
                    + self.weights.gamma * conf
                    - self.weights.delta * r,
                    4,
                ),
            ),
        )
        return {"algorithm_version": self.version, "martin_score": score}
