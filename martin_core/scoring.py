"""
Martin Score Engine
===================
Implements the Martin Score formula:

    M_i = alpha * S_i  +  beta * P_rec(i)  +  gamma * C_i  -  delta * Risk_i

where:
    S_i    = weighted feature score across 9 dimensions
    P_rec  = sigmoid(recovery_logit) — estimated recovery probability
    C_i    = confidence in the data [0, 1]
    Risk_i = normalized risk factor [0, 1]
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import exp

# ---------------------------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------------------------

FEATURES: tuple[str, ...] = (
    "market_activity",
    "liquidity",
    "volume",
    "onchain_activity",
    "developer_activity",
    "exchange_activity",
    "project_health",
    "recovery_evidence",
    "ownership_evidence",
)

DEFAULT_WEIGHTS: dict[str, float] = {
    "market_activity":    0.12,
    "liquidity":          0.12,
    "volume":             0.08,
    "onchain_activity":   0.15,
    "developer_activity": 0.10,
    "exchange_activity":  0.08,
    "project_health":     0.10,
    "recovery_evidence":  0.15,
    "ownership_evidence": 0.10,
}

assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1"

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Candidate:
    """A crypto asset candidate for scoring."""
    asset_id: str
    features: Mapping[str, float] = field(default_factory=dict)
    risk: float = 0.0       # [0, 1] — higher = riskier
    confidence: float = 0.0  # [0, 1] — higher = more data available

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk", clamp(self.risk))
        object.__setattr__(self, "confidence", clamp(self.confidence))


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def clamp(x: float) -> float:
    """Clamp a value to [0, 1]."""
    return max(0.0, min(1.0, float(x)))


def sigmoid(x: float) -> float:
    """Numerically stable sigmoid function."""
    if x >= 0:
        return 1.0 / (1.0 + exp(-x))
    e = exp(x)
    return e / (1.0 + e)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def base_score(
    candidate: Candidate,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> float:
    """Compute the weighted base feature score S_i."""
    return sum(
        weights[k] * clamp(candidate.features.get(k, 0.0))
        for k in FEATURES
    )


def recovery_probability(candidate: Candidate) -> float:
    """
    Estimate P_rec(i) = sigma(logit) where the logit combines
    recovery and ownership evidence minus risk.
    """
    rec = clamp(candidate.features.get("recovery_evidence", 0.0))
    own = clamp(candidate.features.get("ownership_evidence", 0.0))
    logit = 2.0 * rec + 1.5 * own - 2.0 * candidate.risk
    return sigmoid(logit)


def martin_score(
    candidate: Candidate,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
    alpha: float = 0.60,
    beta: float = 0.25,
    gamma: float = 0.15,
    delta: float = 0.50,
) -> float:
    """
    Compute the Martin Score for a single candidate.

    M_i = alpha * S_i + beta * P_rec(i) + gamma * C_i - delta * Risk_i

    Returns a value in [0, 1].
    """
    s = base_score(candidate, weights)
    p_rec = recovery_probability(candidate)
    c = candidate.confidence
    risk = candidate.risk

    raw = alpha * s + beta * p_rec + gamma * c - delta * risk
    return clamp(raw)


def rank_candidates(
    candidates: list[Candidate],
    weights: dict[str, float] = DEFAULT_WEIGHTS,
    top_k: int | None = None,
) -> list[tuple[Candidate, float]]:
    """
    Score and rank a list of candidates, returning (candidate, score) pairs
    sorted descending by score. Optionally limit to top_k results.
    """
    scored = [(c, martin_score(c, weights)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    if top_k is not None:
        scored = scored[:top_k]
    return scored
