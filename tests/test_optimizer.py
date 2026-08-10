"""
Tests — QUBO Builder and Optimizer
"""

import pytest

from martin_core.optimizer import exact_select, greedy_select, select
from martin_core.qubo import build_cardinality_qubo, evaluate_qubo, selected_assets
from martin_core.scoring import Candidate

# ── QUBO tests ───────────────────────────────────────────────

class TestQUBO:
    def test_qubo_shape(self):
        qubo = build_cardinality_qubo(["a", "b", "c"], [0.5, 0.8, 0.3], k=1)
        assert qubo.Q.shape == (3, 3)
        assert qubo.n == 3

    def test_qubo_evaluate_feasible(self):
        qubo = build_cardinality_qubo(["a", "b"], [0.9, 0.1], k=1)
        # Selecting 'a' (bit pattern [1,0]) should be lower cost than [0,1]
        obj_a = evaluate_qubo(qubo, [1, 0])
        obj_b = evaluate_qubo(qubo, [0, 1])
        assert obj_a < obj_b

    def test_qubo_evaluate_infeasible_penalized(self):
        qubo = build_cardinality_qubo(["a", "b", "c"], [0.5, 0.5, 0.5], k=1)
        # Both selected violates cardinality — should have high penalty
        infeasible = evaluate_qubo(qubo, [1, 1, 0])
        feasible   = evaluate_qubo(qubo, [1, 0, 0])
        assert infeasible > feasible

    def test_qubo_constant_positive(self):
        qubo = build_cardinality_qubo(["a", "b"], [0.5, 0.5], k=1)
        assert qubo.constant > 0

    def test_selected_assets(self):
        qubo = build_cardinality_qubo(["x", "y", "z"], [0.1, 0.9, 0.5], k=1)
        assets = selected_assets(qubo, [0, 1, 0])
        assert assets == ["y"]


# ── Optimizer tests ──────────────────────────────────────────

class TestExactOptimizer:
    def test_selects_highest_score_k1(self):
        result = exact_select(["a", "b", "c"], [0.1, 0.9, 0.5], k=1)
        assert result.asset_ids == ["b"]
        assert result.solver == "exact_brute_force"

    def test_selects_k2(self):
        result = exact_select(["a", "b", "c", "d"], [0.1, 0.9, 0.8, 0.2], k=2)
        assert set(result.asset_ids) == {"b", "c"}

    def test_k_equals_n(self):
        result = exact_select(["a", "b", "c"], [0.5, 0.5, 0.5], k=3)
        assert set(result.asset_ids) == {"a", "b", "c"}

    def test_k_zero(self):
        result = exact_select(["a", "b"], [0.5, 0.5], k=0)
        assert result.asset_ids == []

    def test_invalid_k_raises(self):
        with pytest.raises(ValueError):
            exact_select(["a", "b"], [0.5, 0.5], k=5)


class TestGreedyOptimizer:
    def test_greedy_selects_top_k(self):
        result = greedy_select(["a", "b", "c", "d"], [0.1, 0.9, 0.8, 0.2], k=2)
        assert set(result.asset_ids) == {"b", "c"}
        assert result.solver == "greedy"

    def test_greedy_large_n(self):
        n = 50
        ids = [f"asset_{i}" for i in range(n)]
        scores = [i / n for i in range(n)]  # asset_49 has highest score
        result = greedy_select(ids, scores, k=3)
        assert "asset_49" in result.asset_ids


class TestAutoSelect:
    def test_auto_dispatches_exact_for_small_n(self):
        candidates = [
            Candidate(f"c{i}", {"recovery_evidence": i/10}, 0.0, 1.0)
            for i in range(5)
        ]
        result = select(candidates, k=2)
        assert result.solver == "exact_brute_force"

    def test_auto_dispatches_greedy_for_large_n(self):
        candidates = [
            Candidate(f"c{i}", {"recovery_evidence": i/100}, 0.0, 1.0)
            for i in range(25)
        ]
        result = select(candidates, k=5)
        assert result.solver == "greedy"
