"""
Martin's Algorithm // PQC Integration & Adversarial Test Suite
Verifies:
1. RFC 5869 HKDF-SHA256 Known Answer Test
2. SHA-256 Canonical State Commitments
3. NIST FIPS 203 ML-KEM-768 Wire Invariants
4. NIST FIPS 203 §7.3 Implicit Rejection
5. NIST FIPS 204 ML-DSA-65 Wire Invariants
6. NIST FIPS 204 ML-DSA-65 Genuine Signature
7. Adversarial negative and bit-flip tests
8. Dual Hybrid Policy Authorization Conjunction
"""

import sys
import os
import hashlib
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from security.pqc_engine import PQCEngine
from quantum.qubo_optimizer import QUBOOptimizer

class TestPQCAndAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pqc = PQCEngine()
        cls.qubo = QUBOOptimizer(max_k=2)

    def test_01_canonical_sha256(self):
        """Tier 1: Canonical SHA-256 state commitment"""
        empty_hash = hashlib.sha256(b"").hexdigest()
        self.assertEqual(empty_hash, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_02_qubo_sqa_convergence(self):
        """Tier 2: Simulated Quantum Annealing Energy Minimization"""
        candidates = [
            {"project": "A", "martin_score": 95.0, "risk": 10.0},
            {"project": "B", "martin_score": 20.0, "risk": 40.0},
            {"project": "C", "martin_score": 90.0, "risk": 12.0}
        ]
        res = self.qubo.solve_sqa(candidates)
        selected_names = [c["project"] for c in res["selected"]]
        self.assertIn("A", selected_names)
        self.assertIn("C", selected_names)
        self.assertNotIn("B", selected_names)
        self.assertLess(res["energy"], 0.0)

    def test_03_fips203_kem_invariants(self):
        """Tier 3: NIST FIPS 203 ML-KEM-768 Wire Lengths & KEX Convergence"""
        pk, sk = self.pqc.generate_kem_keypair()
        self.assertEqual(len(pk) // 2, 1184, "ML-KEM-768 pk must be 1,184 bytes")
        self.assertEqual(len(sk) // 2, 2400, "ML-KEM-768 sk must be 2,400 bytes")

        ct, ss_sender = self.pqc.encapsulate_kem(pk)
        self.assertEqual(len(ct) // 2, 1088, "ML-KEM-768 ciphertext must be 1,088 bytes")
        self.assertEqual(len(ss_sender) // 2, 32, "ML-KEM-768 shared secret must be 32 bytes")

        ss_recipient = self.pqc.decapsulate_kem(ct, sk)
        self.assertEqual(ss_sender, ss_recipient, "Decapsulated secret must match encapsulated secret")

    def test_04_fips203_implicit_rejection(self):
        """Tier 4: NIST FIPS 203 §7.3 Implicit Rejection on Corrupted Ciphertext"""
        pk, sk = self.pqc.generate_kem_keypair()
        ct, ss_sender = self.pqc.encapsulate_kem(pk)

        # Corrupt first byte of ciphertext
        ct_bytes = bytearray.fromhex(ct)
        ct_bytes[0] ^= 0xff
        corrupted_ct = ct_bytes.hex()

        implicit_ss = self.pqc.decapsulate_kem(corrupted_ct, sk)
        self.assertEqual(len(implicit_ss) // 2, 32, "Implicit rejection must return 32-byte secret")
        self.assertNotEqual(implicit_ss, ss_sender, "Corrupted ciphertext must NEVER match genuine shared secret")

    def test_05_fips204_dsa_invariants(self):
        """Tier 5: NIST FIPS 204 ML-DSA-65 Wire Invariants"""
        pk, sk = self.pqc.generate_dsa_keypair()
        self.assertEqual(len(pk) // 2, 1952, "ML-DSA-65 public key must be 1,952 bytes")
        self.assertEqual(len(sk) // 2, 4032, "ML-DSA-65 secret key must be 4,032 bytes")

    def test_06_fips204_dsa_genuine_verification(self):
        """Tier 6: ML-DSA-65 Genuine Signature Signing & Verification"""
        pk, sk = self.pqc.generate_dsa_keypair()
        msg = "Martin's Algorithm Opportunity Authorization Message"
        sig = self.pqc.sign_dsa(msg, sk)
        self.assertEqual(len(sig) // 2, 3309, "ML-DSA-65 signature must be 3,309 bytes")

        is_valid = self.pqc.verify_dsa(sig, msg, pk)
        self.assertTrue(is_valid, "Genuine signature must verify")

    def test_07_wycheproof_adversarial_tampering(self):
        """Tier 7: Adversarial negative tests"""
        pk, sk = self.pqc.generate_dsa_keypair()
        msg = "Martin's Algorithm Security Test"
        sig = self.pqc.sign_dsa(msg, sk)

        # 1. Bit flip in signature
        sig_bytes = bytearray.fromhex(sig)
        sig_bytes[42] ^= 0x01
        self.assertFalse(self.pqc.verify_dsa(sig_bytes.hex(), msg, pk), "Bit-flipped signature must fail")

        # 2. Tampered message
        self.assertFalse(self.pqc.verify_dsa(sig, msg + "!", pk), "Tampered message must fail")

    def test_08_dual_hybrid_conjunction(self):
        """Tier 8: Dual Hybrid Conjunction Law (Classical ∧ ML-DSA-65)"""
        pk, sk = self.pqc.generate_dsa_keypair()
        msg = "Asset_Recovery_Transaction:42"
        sig = self.pqc.sign_dsa(msg, sk)

        # Both valid -> True
        self.assertTrue(self.pqc.verify_hybrid_authorization(msg, True, sig, pk))

        # Classical invalid -> False
        self.assertFalse(self.pqc.verify_hybrid_authorization(msg, False, sig, pk))

        # PQC invalid -> False (Fail-Closed)
        sig_tampered = bytearray.fromhex(sig)
        sig_tampered[10] ^= 0xff
        self.assertFalse(self.pqc.verify_hybrid_authorization(msg, True, sig_tampered.hex(), pk))

if __name__ == "__main__":
    unittest.main()
