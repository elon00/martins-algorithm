"""
QUBO Builder
============
Constructs a Quadratic Unconstrained Binary Optimization (QUBO) matrix
for the Martin candidate-selection problem.

Problem:
    Select exactly K assets from N candidates to maximize total Martin Score,
    subject to the cardinality constraint sum(q_i) = K.

QUBO formulation:
    min_q  C(q) = -sum_i M_i*q_i  +  lambda*(sum_i q_i - K)^2

    Expanding the penalty:
        Q_{ii} = -M_i + lambda*(1 - 2K)
        Q_{ij} = 2*lambda  for i < j
        constant = lambda * K^2
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class QUBO:
    """Upper-triangular QUBO matrix with metadata."""
    Q: np.ndarray          # shape (N, N), upper-triangular
    constant: float        # scalar offset for objective value
    asset_ids: list[str]   # ordered list of asset identifiers

    @property
    def n(self) -> int:
        return len(self.asset_ids)


def build_cardinality_qubo(
    asset_ids: list[str],
    scores: list[float],
    k: int,
    penalty: float = 2.0,
) -> QUBO:
    """
    Build a QUBO for selecting exactly k assets that maximize Martin Score.

    Args:
        asset_ids: List of asset identifiers.
        scores:    Martin Scores for each asset (same order as asset_ids).
        k:         Number of assets to select.
        penalty:   Lagrange multiplier for the cardinality constraint.
                   Recommended: penalty > max(scores) to ensure feasibility.

    Returns:
        QUBO object with upper-triangular Q matrix.
    """
    n = len(scores)
    if n != len(asset_ids):
        raise ValueError("asset_ids and scores must have equal length.")
    if not (0 <= k <= n):
        raise ValueError(f"k must satisfy 0 <= k <= n, got k={k}, n={n}.")
    if penalty <= 0:
        raise ValueError("penalty must be positive.")

    Q = np.zeros((n, n), dtype=np.float64)

    # Diagonal: objective + penalty*(1 - 2K)*q_i
    for i, s in enumerate(scores):
        Q[i, i] = -float(s) + penalty * (1 - 2 * k)

    # Off-diagonal (upper-triangular): cross-penalty 2*lambda*q_i*q_j
    for i in range(n):
        for j in range(i + 1, n):
            Q[i, j] = 2.0 * penalty

    constant = penalty * float(k ** 2)
    return QUBO(Q=Q, constant=constant, asset_ids=list(asset_ids))


def evaluate_qubo(qubo: QUBO, bits: list[int]) -> float:
    """
    Evaluate the QUBO objective for a given binary assignment.

    Args:
        qubo: QUBO object.
        bits: Binary list of length N where bits[i] in {0, 1}.

    Returns:
        Objective value C(q) = x^T Q x + constant.
    """
    if len(bits) != qubo.n:
        raise ValueError(f"bits length {len(bits)} != QUBO size {qubo.n}.")
    x = np.asarray(bits, dtype=np.float64)
    return float(x @ qubo.Q @ x) + qubo.constant


def selected_assets(qubo: QUBO, bits: list[int]) -> list[str]:
    """Return the asset_ids selected by a binary assignment."""
    return [qubo.asset_ids[i] for i, b in enumerate(bits) if b == 1]
