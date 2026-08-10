"""
Fail-Closed Permission & Policy Engine
=======================================
All actions in Martin's Algorithm must pass through this engine.

Design principles:
  - Fail-closed: unknown = denied
  - No seed phrases or private keys are ever accepted, stored, or logged
  - Every value-transfer action requires explicit user approval
  - High-risk actions require additional confirmation
  - AI agents may propose actions; signing stays with the user
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    READ_ONLY = "read_only"   # scanning, data fetching — no approval needed
    LOW       = "low"         # alert generation — no approval needed
    MEDIUM    = "medium"      # preparing a claim transaction — requires approval
    HIGH      = "high"        # sending a transaction — requires approval
    CRITICAL  = "critical"    # multi-sig, large value — requires approval + 2FA signal


@dataclass(frozen=True)
class ActionRequest:
    """Represents a proposed action by an agent or the system."""
    action: str                  # human-readable action description
    asset_id: str | None         # asset involved, if any
    value: float                 # monetary value involved (0 for read-only)
    risk: RiskLevel
    user_approved: bool = False  # set True only after explicit user confirmation
    metadata: dict | None = None


@dataclass(frozen=True)
class PolicyDecision:
    approved: bool
    reason: str
    risk: RiskLevel
    action: str


class PolicyEngine:
    """
    Fail-closed permission engine.

    Rules (evaluated in order — first match wins):
      1. Negative value → DENY
      2. CRITICAL → requires user_approved
      3. HIGH     → requires user_approved
      4. Any value > 0 → requires user_approved
      5. MEDIUM with value > 0 → requires user_approved
      6. READ_ONLY / LOW with value == 0 → ALLOW
      7. Everything else → DENY
    """

    def authorize(self, request: ActionRequest) -> PolicyDecision:
        # Rule 1: sanity check
        if request.value < 0:
            return PolicyDecision(
                approved=False,
                reason="Negative value rejected.",
                risk=request.risk,
                action=request.action,
            )

        # Rule 2-3: CRITICAL / HIGH always need user approval
        if request.risk in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            if not request.user_approved:
                return PolicyDecision(
                    approved=False,
                    reason=f"{request.risk.value.upper()} action requires explicit user approval.",
                    risk=request.risk,
                    action=request.action,
                )

        # Rule 4: any monetary value needs user approval
        if request.value > 0 and not request.user_approved:
            return PolicyDecision(
                approved=False,
                reason="User approval required for any value-transfer action.",
                risk=request.risk,
                action=request.action,
            )

        # Rule 5: MEDIUM with value needs approval
        if request.risk == RiskLevel.MEDIUM and request.value > 0 and not request.user_approved:
            return PolicyDecision(
                approved=False,
                reason="MEDIUM risk value action requires user approval.",
                risk=request.risk,
                action=request.action,
            )

        # Rule 6: READ_ONLY / LOW with zero value — allow freely
        if request.risk in (RiskLevel.READ_ONLY, RiskLevel.LOW) and request.value == 0:
            return PolicyDecision(
                approved=True,
                reason="Read-only or low-risk informational action — approved.",
                risk=request.risk,
                action=request.action,
            )

        # Rule 7: anything else with approval = allow
        if request.user_approved:
            return PolicyDecision(
                approved=True,
                reason="User explicitly approved this action.",
                risk=request.risk,
                action=request.action,
            )

        # Default: DENY
        return PolicyDecision(
            approved=False,
            reason="Action did not satisfy any approval policy — denied by default.",
            risk=request.risk,
            action=request.action,
        )

    def check_no_key_in_request(self, data: dict) -> tuple[bool, str]:
        """
        Scan a dictionary for any suspicious fields that might contain
        private keys or seed phrases. Returns (safe, reason).
        """
        forbidden_keys = {
            "private_key", "privatekey", "seed_phrase", "seedphrase",
            "mnemonic", "secret_key", "secretkey", "keystore",
        }
        for k in data:
            if k.lower().replace(" ", "_") in forbidden_keys:
                return False, f"Forbidden field detected: '{k}'. Private keys/seed phrases are never accepted."
        return True, "No sensitive fields detected."
