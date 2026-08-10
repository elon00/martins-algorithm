"""
Optimizer
=========
Classical reference optimizers for the Martin QUBO.

Two solvers are provided:
  1. exact_select   — Brute-force exact solution for small N (N <= 20).
                      This is the ground-truth baseline against which any
                      future quantum optimizer must be benchmarked.
  2. greedy_select  — O(N log N) greedy approximation for large N.

Quantum slot:
  When a QAOA or other quantum optimizer is available, it must be validated
  against exact_select on small instances before being deployed.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .qubo import QUBO, build_cardinality_qubo, evaluate_qubo
from .scoring import Candidate, martin_score


@dataclass(frozen=True)
class OptimizationResult:
    asset_ids: list[str]
    objective: float
    solver: str
    n_candidates: int
    k: int


# ---------------------------------------------------------------------------
# Exact solver  (ground-truth baseline)
# ---------------------------------------------------------------------------

EXACT_MAX_N = 20  # beyond this, use greedy


def exact_select(
    asset_ids: list[str],
    scores: list[float],
    k: int,
    penalty: float = 2.0,
) -> OptimizationResult:
    """
    Exact brute-force QUBO solver. Guaranteed optimal for small N.

    Complexity: O(C(N, k)) — feasible only for N <= 20.
    """
    n = len(scores)
    if n != len(asset_ids):
        raise ValueError("asset_ids and scores must have equal length.")
    if k < 0 or k > n:
        raise ValueError(f"Invalid k={k} for n={n}.")
    if n > EXACT_MAX_N:
        raise ValueError(
            f"exact_select supports N <= {EXACT_MAX_N}. Use greedy_select for larger inputs."
        )

    qubo = build_cardinality_qubo(asset_ids, scores, k, penalty)

    best_bits: list[int] = []
    best_obj: float = float("inf")

    for chosen in combinations(range(n), k):
        bits = [0] * n
        for i in chosen:
            bits[i] = 1
        obj = evaluate_qubo(qubo, bits)
        if obj < best_obj:
            best_obj = obj
            best_bits = bits[:]

    selected = [asset_ids[i] for i, b in enumerate(best_bits) if b == 1]
    return OptimizationResult(
        asset_ids=selected,
        objective=best_obj,
        solver="exact_brute_force",
        n_candidates=n,
        k=k,
    )


# ---------------------------------------------------------------------------
# Greedy solver  (large N approximation)
# ---------------------------------------------------------------------------

def greedy_select(
    asset_ids: list[str],
    scores: list[float],
    k: int,
) -> OptimizationResult:
    """
    Greedy O(N log N) approximation: simply pick the top-k scoring assets.

    Not optimal but runs in linear time for any N.
    """
    n = len(scores)
    if n != len(asset_ids):
        raise ValueError("asset_ids and scores must have equal length.")
    if k < 0 or k > n:
        raise ValueError(f"Invalid k={k} for n={n}.")

    ranked = sorted(zip(scores, asset_ids), reverse=True)
    selected_ids = [aid for _, aid in ranked[:k]]

    # Compute QUBO objective for reporting consistency
    qubo = build_cardinality_qubo(asset_ids, scores, k)
    bits = [1 if aid in set(selected_ids) else 0 for aid in asset_ids]
    obj = evaluate_qubo(qubo, bits)

    return OptimizationResult(
        asset_ids=selected_ids,
        objective=obj,
        solver="greedy",
        n_candidates=n,
        k=k,
    )


# ---------------------------------------------------------------------------
# Auto-dispatch
# ---------------------------------------------------------------------------

def select(
    candidates: list[Candidate],
    k: int,
    penalty: float = 2.0,
) -> OptimizationResult:
    """
    Auto-dispatch to exact or greedy based on N.

    This is the main entry point for the optimizer.
    """
    asset_ids = [c.asset_id for c in candidates]
    scores = [martin_score(c) for c in candidates]
    n = len(candidates)

    if n <= EXACT_MAX_N:
        return exact_select(asset_ids, scores, k, penalty)
    else:
        return greedy_select(asset_ids, scores, k)
