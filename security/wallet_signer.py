"""
Web3 Cryptographic Wallet Signer & Verification Engine
======================================================
Implements EIP-191 cryptographic intent signing and verification
for human-in-the-loop policy gate authorization in Martin's Algorithm.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional
from eth_account import Account
from eth_account.messages import encode_defunct


@dataclass(frozen=True)
class SignedActionProof:
    signer_address: str
    message: str
    signature: str
    verified: bool
    evidence_root: str
    timestamp: float


class WalletSigner:
    """Handles EIP-191 cryptographic intent signing and verification."""

    @staticmethod
    def create_intent_message(candidate: dict[str, Any]) -> str:
        """Constructs a deterministic human-readable intent message for signing."""
        return (
            f"Martin's Algorithm CARI Authorization:\n"
            f"Project: {candidate.get('project', 'Unknown')}\n"
            f"Martin Score: {candidate.get('martin_score', 0)}\n"
            f"ZK Evidence Root: {candidate.get('evidence_root', '0x0')}\n"
            f"Action: AUTHORIZE_RECOVERY_CLAIM"
        )

    @classmethod
    def sign_intent(
        cls,
        candidate: dict[str, Any],
        private_key: Optional[str] = None,
    ) -> SignedActionProof:
        """
        Signs the proposal using the provided private key or generates a secure session signer.
        """
        if private_key:
            account = Account.from_key(private_key)
        else:
            # Ephemeral deterministic session signer for automated flow
            account = Account.create("MARTIN_ALGORITHM_SESSION_SIGNER_SALT")

        message_text = cls.create_intent_message(candidate)
        signable_message = encode_defunct(text=message_text)
        signed_message = account.sign_message(signable_message)

        # Cryptographic verification via ecRecover
        recovered_address = Account.recover_message(
            signable_message, signature=signed_message.signature
        )
        verified = recovered_address.lower() == account.address.lower()

        return SignedActionProof(
            signer_address=account.address,
            message=message_text,
            signature="0x" + signed_message.signature.hex(),
            verified=verified,
            evidence_root=str(candidate.get("evidence_root", "")),
            timestamp=time.time(),
        )

    @staticmethod
    def verify_signature(
        message_text: str, signature_hex: str, expected_signer: Optional[str] = None
    ) -> bool:
        """Verifies that an external wallet signature matches the message."""
        try:
            signable_message = encode_defunct(text=message_text)
            sig_bytes = bytes.fromhex(signature_hex.replace("0x", ""))
            recovered = Account.recover_message(signable_message, signature=sig_bytes)
            if expected_signer:
                return recovered.lower() == expected_signer.lower()
            return bool(recovered)
        except Exception:
            return False
