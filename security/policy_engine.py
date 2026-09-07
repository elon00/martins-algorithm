from typing import Dict, Any, Optional
from security.pqc_engine import PQCEngine

class PolicyEngine:
    def __init__(self):
        self.pqc = PQCEngine()

    def evaluate(
        self,
        opt: Dict[str, Any],
        dsa_signature_hex: Optional[str] = None,
        dsa_public_key_hex: Optional[str] = None,
        classical_signature_valid: bool = True
    ) -> Dict[str, Any]:
        """
        Policy Engine with Multi-Tier Validation:
        1. Security threshold (Martin Score >= 50.0)
        2. Status check (RECOVERABLE, MIGRATED, ACTIVE)
        3. Post-Quantum Lattice Hybrid Conjunction Gate
        """
        score = opt.get('martin_score', 0)
        status = opt.get('status')

        if status not in ['RECOVERABLE', 'MIGRATED', 'ACTIVE'] or score < 50.0:
            return {
                'action': 'DENIED',
                'reason': f'Failed Security Threshold (Score: {score}, Status: {status})',
                'pqc_verified': False
            }

        # If PQC signatures are provided, verify dual hybrid conjunction
        if dsa_signature_hex and dsa_public_key_hex:
            msg = f"{opt.get('project')}:{opt.get('evidence_root', '')}:{score}"
            pqc_ok = self.pqc.verify_hybrid_authorization(
                message=msg,
                classical_valid=classical_signature_valid,
                dsa_signature_hex=dsa_signature_hex,
                dsa_public_key_hex=dsa_public_key_hex
            )
            if not pqc_ok:
                return {
                    'action': 'DENIED_PQC_FAIL',
                    'reason': 'Dual Hybrid Post-Quantum Signature Verification Failed (Fail-Closed)',
                    'pqc_verified': False
                }
            return {
                'action': 'PQC_AUTHORIZED',
                'reason': 'Dual Hybrid (Classical + NIST FIPS 204 ML-DSA-65) Authorization Verified',
                'pqc_verified': True
            }

        return {
            'action': 'REQUIRE_HUMAN_APPROVAL',
            'reason': 'Passed AI Checks. Awaiting Post-Quantum Wallet Signature.',
            'pqc_verified': False
        }
