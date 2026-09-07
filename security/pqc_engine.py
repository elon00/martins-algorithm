"""
Martin's Algorithm // Post-Quantum Security Engine
Integrates NIST FIPS 203 ML-KEM-768 and NIST FIPS 204 ML-DSA-65 with Python-native API
Provides:
- Lattice-based Digital Signatures for Autonomous Opportunity Approvals
- Dual Hybrid Conjunction (Classical + PQC Lattice)
- Fail-Closed Abort on Bit-Flip Tampering
"""

import os
import subprocess
import json
from typing import Dict, Any, Optional, Tuple

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
PQC_CLI_PATH = os.path.join(SCRIPTS_DIR, "pqc_cli.mjs")

class PQCError(Exception):
    pass

class PQCEngine:
    def __init__(self, cli_path: str = PQC_CLI_PATH):
        self.cli_path = cli_path

    def _exec_cli(self, *args: str) -> Dict[str, Any]:
        cmd = ["node", self.cli_path] + list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if proc.returncode != 0:
            raise PQCError(f"PQC CLI execution failed: {proc.stderr or proc.stdout}")
        try:
            return json.loads(proc.stdout.strip())
        except json.JSONDecodeError as e:
            raise PQCError(f"Failed to parse PQC CLI output: {proc.stdout}") from e

    # -------------------------------------------------------------------------
    # NIST FIPS 204 ML-DSA-65
    # -------------------------------------------------------------------------
    def generate_dsa_keypair(self, seed_hex: Optional[str] = None) -> Tuple[str, str]:
        args = ["keygen_dsa"]
        if seed_hex:
            args.append(seed_hex)
        res = self._exec_cli(*args)
        return res["publicKeyHex"], res["secretKeyHex"]

    def sign_dsa(self, message: str, secret_key_hex: str) -> str:
        res = self._exec_cli("sign_dsa", message, secret_key_hex)
        return res["signatureHex"]

    def verify_dsa(self, signature_hex: str, message: str, public_key_hex: str) -> bool:
        try:
            res = self._exec_cli("verify_dsa", signature_hex, message, public_key_hex)
            return bool(res.get("valid", False))
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # NIST FIPS 203 ML-KEM-768
    # -------------------------------------------------------------------------
    def generate_kem_keypair(self, seed_hex: Optional[str] = None) -> Tuple[str, str]:
        args = ["keygen_kem"]
        if seed_hex:
            args.append(seed_hex)
        res = self._exec_cli(*args)
        return res["publicKeyHex"], res["secretKeyHex"]

    def encapsulate_kem(self, public_key_hex: str) -> Tuple[str, str]:
        res = self._exec_cli("encaps_kem", public_key_hex)
        return res["ciphertextHex"], res["sharedSecretHex"]

    def decapsulate_kem(self, ciphertext_hex: str, secret_key_hex: str) -> str:
        res = self._exec_cli("decaps_kem", ciphertext_hex, secret_key_hex)
        return res["sharedSecretHex"]

    # -------------------------------------------------------------------------
    # Dual Hybrid Conjunction Verification
    # -------------------------------------------------------------------------
    def verify_hybrid_authorization(
        self,
        message: str,
        classical_valid: bool,
        dsa_signature_hex: str,
        dsa_public_key_hex: str
    ) -> bool:
        """
        Dual Hybrid Conjunction Law:
        Authorization is VALID iff Classical Signature AND PQC ML-DSA-65 Signature BOTH PASS.
        Fail-Closed: Any partial failure rejects the transaction.
        """
        if not classical_valid:
            return False
        return self.verify_dsa(dsa_signature_hex, message, dsa_public_key_hex)
