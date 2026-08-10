"""
Tests — Martin Score Engine
"""

from martin_core.scoring import (
    DEFAULT_WEIGHTS,
    Candidate,
    clamp,
    martin_score,
    rank_candidates,
    sigmoid,
)

# ── Helpers ──────────────────────────────────────────────────

def make_candidate(asset_id="test", **kwargs) -> Candidate:
    features = {
        "market_activity":    kwargs.pop("market_activity",    0.5),
        "liquidity":          kwargs.pop("liquidity",          0.5),
        "volume":             kwargs.pop("volume",             0.5),
        "onchain_activity":   kwargs.pop("onchain_activity",   0.5),
        "developer_activity": kwargs.pop("developer_activity", 0.5),
        "exchange_activity":  kwargs.pop("exchange_activity",  0.5),
        "project_health":     kwargs.pop("project_health",     0.5),
        "recovery_evidence":  kwargs.pop("recovery_evidence",  0.5),
        "ownership_evidence": kwargs.pop("ownership_evidence", 0.5),
    }
    risk       = kwargs.pop("risk", 0.0)
    confidence = kwargs.pop("confidence", 1.0)
    return Candidate(asset_id=asset_id, features=features, risk=risk, confidence=confidence)


# ── Unit tests ───────────────────────────────────────────────

class TestClamp:
    def test_within_range(self):
        assert clamp(0.5) == 0.5

    def test_below_zero(self):
        assert clamp(-1.0) == 0.0

    def test_above_one(self):
        assert clamp(2.0) == 1.0

    def test_boundary_zero(self):
        assert clamp(0.0) == 0.0

    def test_boundary_one(self):
        assert clamp(1.0) == 1.0


class TestSigmoid:
    def test_zero(self):
        assert abs(sigmoid(0.0) - 0.5) < 1e-9

    def test_large_positive(self):
        assert sigmoid(100.0) > 0.999

    def test_large_negative(self):
        assert sigmoid(-100.0) < 0.001


class TestMartinScore:
    def test_output_bounded_zero_one(self):
        for _ in range(20):
            import random
            c = Candidate(
                "rand",
                features={k: random.random() for k in DEFAULT_WEIGHTS},
                risk=random.random(),
                confidence=random.random(),
            )
            s = martin_score(c)
            assert 0.0 <= s <= 1.0, f"Score out of bounds: {s}"

    def test_all_zeros(self):
        c = Candidate("z", features={k: 0.0 for k in DEFAULT_WEIGHTS}, risk=0.0, confidence=0.0)
        s = martin_score(c)
        assert 0.0 <= s <= 1.0

    def test_all_ones(self):
        c = Candidate("o", features={k: 1.0 for k in DEFAULT_WEIGHTS}, risk=0.0, confidence=1.0)
        s = martin_score(c)
        assert 0.0 <= s <= 1.0

    def test_high_recovery_evidence_scores_higher(self):
        low  = make_candidate("low",  recovery_evidence=0.0, ownership_evidence=0.0, risk=0.5)
        high = make_candidate("high", recovery_evidence=1.0, ownership_evidence=1.0, risk=0.0)
        assert martin_score(high) > martin_score(low)

    def test_high_risk_reduces_score(self):
        safe   = make_candidate("safe",   risk=0.0)
        risky  = make_candidate("risky",  risk=1.0)
        assert martin_score(safe) > martin_score(risky)

    def test_confidence_matters(self):
        lo = make_candidate("lo", confidence=0.0)
        hi = make_candidate("hi", confidence=1.0)
        assert martin_score(hi) > martin_score(lo)


class TestRankCandidates:
    def test_ranking_is_descending(self):
        c1 = make_candidate("c1", recovery_evidence=0.9, risk=0.0, confidence=1.0)
        c2 = make_candidate("c2", recovery_evidence=0.1, risk=0.8, confidence=0.2)
        c3 = make_candidate("c3", recovery_evidence=0.5, risk=0.3, confidence=0.6)
        ranked = rank_candidates([c1, c2, c3])
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_limits_results(self):
        candidates = [make_candidate(f"c{i}") for i in range(10)]
        ranked = rank_candidates(candidates, top_k=3)
        assert len(ranked) == 3

    def test_single_candidate(self):
        c = make_candidate("solo")
        ranked = rank_candidates([c])
        assert len(ranked) == 1
        assert ranked[0][0].asset_id == "solo"
