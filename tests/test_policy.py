"""
Tests — Policy Engine
"""

import pytest
from martin_core.policy import ActionRequest, PolicyEngine, RiskLevel


@pytest.fixture
def engine():
    return PolicyEngine()


class TestPolicyEngine:
    def test_read_only_with_zero_value_approved(self, engine):
        req = ActionRequest("scan", None, 0.0, RiskLevel.READ_ONLY)
        decision = engine.authorize(req)
        assert decision.approved is True

    def test_negative_value_denied(self, engine):
        req = ActionRequest("bad", None, -1.0, RiskLevel.LOW)
        decision = engine.authorize(req)
        assert decision.approved is False
        assert "negative" in decision.reason.lower()

    def test_high_risk_without_approval_denied(self, engine):
        req = ActionRequest("transfer", "TKN", 100.0, RiskLevel.HIGH, user_approved=False)
        decision = engine.authorize(req)
        assert decision.approved is False

    def test_high_risk_with_approval_approved(self, engine):
        req = ActionRequest("transfer", "TKN", 100.0, RiskLevel.HIGH, user_approved=True)
        decision = engine.authorize(req)
        assert decision.approved is True

    def test_critical_without_approval_denied(self, engine):
        req = ActionRequest("multisig_tx", "BTC", 999.0, RiskLevel.CRITICAL, user_approved=False)
        decision = engine.authorize(req)
        assert decision.approved is False

    def test_any_value_without_approval_denied(self, engine):
        req = ActionRequest("claim", "TKN", 1.0, RiskLevel.MEDIUM, user_approved=False)
        decision = engine.authorize(req)
        assert decision.approved is False

    def test_low_risk_zero_value_approved(self, engine):
        req = ActionRequest("alert", "TKN", 0.0, RiskLevel.LOW)
        decision = engine.authorize(req)
        assert decision.approved is True

    def test_decision_has_reason(self, engine):
        req = ActionRequest("x", None, 0.0, RiskLevel.READ_ONLY)
        decision = engine.authorize(req)
        assert isinstance(decision.reason, str)
        assert len(decision.reason) > 0


class TestKeyScanner:
    def test_detects_private_key(self, engine):
        safe, reason = engine.check_no_key_in_request({"private_key": "0xdeadbeef"})
        assert safe is False
        assert "private_key" in reason.lower()

    def test_detects_seed_phrase(self, engine):
        safe, _ = engine.check_no_key_in_request({"seed_phrase": "word1 word2"})
        assert safe is False

    def test_clean_dict_is_safe(self, engine):
        safe, _ = engine.check_no_key_in_request({"asset_id": "BTC", "value": 0})
        assert safe is True
