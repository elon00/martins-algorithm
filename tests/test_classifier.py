"""
Tests — Asset Classifier
"""

import pytest
from martin_core.classifier import AssetStatus, classify, batch_classify
from martin_core.scoring import Candidate


def c(asset_id, features=None, risk=0.0, confidence=0.8):
    return Candidate(asset_id, features or {}, risk, confidence)


class TestClassifier:
    def test_unknown_when_confidence_too_low(self):
        candidate = c("x", confidence=0.05)
        result = classify(candidate)
        assert result.status == AssetStatus.UNKNOWN

    def test_recoverable_with_strong_evidence(self):
        candidate = c(
            "rec",
            features={"recovery_evidence": 0.9, "ownership_evidence": 0.7},
            confidence=0.8,
        )
        result = classify(candidate)
        assert result.status == AssetStatus.RECOVERABLE

    def test_migrated_with_migration_evidence(self):
        candidate = c(
            "mig",
            features={"migration_evidence": 0.85},
            confidence=0.8,
        )
        result = classify(candidate)
        assert result.status == AssetStatus.MIGRATED

    def test_dead_with_zero_features(self):
        candidate = c(
            "dead",
            features={"liquidity": 0.0, "developer_activity": 0.0, "recovery_evidence": 0.0},
            risk=0.9,
            confidence=0.8,
        )
        result = classify(candidate)
        assert result.status in (AssetStatus.DEAD, AssetStatus.ABANDONED, AssetStatus.DORMANT)

    def test_result_has_all_fields(self):
        candidate = c("test")
        result = classify(candidate)
        assert result.asset_id == "test"
        assert isinstance(result.status, AssetStatus)
        assert 0.0 <= result.martin_score <= 1.0
        assert 0.0 <= result.recovery_probability <= 1.0
        assert isinstance(result.explanation, str)

    def test_batch_classify_sorted_descending(self):
        candidates = [
            c("hi",  features={"recovery_evidence": 0.9, "ownership_evidence": 0.9}, confidence=0.9),
            c("mid", features={"recovery_evidence": 0.4}, confidence=0.6),
            c("lo",  features={}, risk=0.9, confidence=0.5),
        ]
        results = batch_classify(candidates)
        scores = [r.martin_score for r in results]
        assert scores == sorted(scores, reverse=True)
