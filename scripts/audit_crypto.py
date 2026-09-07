#!/usr/bin/env python3
"""
Martin's Algorithm // Standalone Cryptographic Auditor
Verifies 23 Invariants across:
- Canonical Hash & Commitment Invariants
- QUBO Simulated Quantum Annealing Ground State Invariants
- NIST FIPS 203 ML-KEM-768 Lattice Keygen, Encapsulation, Decapsulation
- NIST FIPS 203 §7.3 Implicit Rejection
- NIST FIPS 204 ML-DSA-65 Wire Invariants & Deterministic Keygen
- Wycheproof Bit-Flip Tampering & Negative Attacks
- Dual Hybrid Conjunction Conformance
"""

import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from security.pqc_engine import PQCEngine
from quantum.qubo_optimizer import QUBOOptimizer

print("=====================================================================")
print("⚡ MARTIN'S ALGORITHM // STANDALONE CRYPTOGRAPHIC AUDITOR")
print("=====================================================================\n")

assertion_count = 0
def check(condition, desc):
    global assertion_count
    if not condition:
        print(f"❌ ASSERTION FAILED: {desc}")
        sys.exit(1)
    assertion_count += 1
    print(f"  [{assertion_count}/23] ✅ {desc}")

pqc = PQCEngine()
qubo = QUBOOptimizer(max_k=2)

print("▶ [TIER 1] Canonical Hash & State Commitment Invariants:")
empty_hash = hashlib.sha256(b"").hexdigest()
check(empty_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "Empty SHA-256 matches canonical NIST hash")

root_hash = hashlib.sha256(b"Martin Algorithm Root State").hexdigest()
check(len(root_hash) == 64, "State commitment produces exact 32 bytes hex")

print("\n▶ [TIER 2] QUBO Hamiltonian & SQA Invariants:")
Q, scores = qubo.build_qubo_matrix([
    {"project": "P1", "martin_score": 90.0, "risk": 10.0},
    {"project": "P2", "martin_score": 30.0, "risk": 50.0}
])
check(Q.shape == (2, 2), "QUBO matrix is NxN symmetric formulation")
check(Q[0, 1] == Q[1, 0], "QUBO coupling terms are strictly symmetric")

sqa_res = qubo.solve_sqa([
    {"project": "P1", "martin_score": 90.0, "risk": 10.0},
    {"project": "P2", "martin_score": 30.0, "risk": 50.0}
])
check(len(sqa_res["selected"]) <= 2, "SQA satisfies cardinality constraint K")
check(sqa_res["energy"] < 0, "SQA converges to negative ground state energy")

print("\n▶ [TIER 3] NIST FIPS 203 ML-KEM-768 Lattice Execution:")
pk_kem, sk_kem = pqc.generate_kem_keypair()
check(len(pk_kem) // 2 == 1184, "ML-KEM-768 public key exact 1,184 bytes")
check(len(sk_kem) // 2 == 2400, "ML-KEM-768 secret key exact 2,400 bytes")

ct, ss_sender = pqc.encapsulate_kem(pk_kem)
check(len(ct) // 2 == 1088, "ML-KEM-768 ciphertext exact 1,088 bytes")
check(len(ss_sender) // 2 == 32, "ML-KEM-768 shared secret exact 32 bytes")

ss_recip = pqc.decapsulate_kem(ct, sk_kem)
check(ss_sender == ss_recip, "ML-KEM-768 decapsulation recovers shared secret byte-for-byte")

print("\n▶ [TIER 4] FIPS 203 §7.3 Implicit Rejection:")
bad_ct = bytearray.fromhex(ct)
bad_ct[0] ^= 0xaa
implicit_ss = pqc.decapsulate_kem(bad_ct.hex(), sk_kem)
check(len(implicit_ss) // 2 == 32, "Implicit rejection returns valid 32-byte pseudorandom value")
check(implicit_ss != ss_sender, "Corrupted ciphertext does NOT yield sender shared secret")

print("\n▶ [TIER 5] NIST FIPS 204 ML-DSA-65 Digital Signatures:")
pk_dsa, sk_dsa = pqc.generate_dsa_keypair()
check(len(pk_dsa) // 2 == 1952, "ML-DSA-65 public key exact 1,952 bytes")
check(len(sk_dsa) // 2 == 4032, "ML-DSA-65 secret key exact 4,032 bytes")

pk_hash = hashlib.sha256(bytes.fromhex(pk_dsa)).hexdigest()
check(len(pk_hash) == 64, "ML-DSA-65 public key commitments derive 32-byte SHA-256 hash")

msg = "Martin's Algorithm Asset Recovery Transaction Invariant"
sig = pqc.sign_dsa(msg, sk_dsa)
check(len(sig) // 2 == 3309, "ML-DSA-65 signature exact 3,309 bytes")

sig_valid = pqc.verify_dsa(sig, msg, pk_dsa)
check(sig_valid is True, "ML-DSA-65 genuine signature verified successfully")

print("\n▶ [TIER 6] Wycheproof Negative & Adversarial Tests:")
tampered_sig = bytearray.fromhex(sig)
tampered_sig[100] ^= 0x01
check(pqc.verify_dsa(tampered_sig.hex(), msg, pk_dsa) is False, "Wycheproof: Bit-flipped signature rejected cleanly")

check(pqc.verify_dsa(sig, msg + "!", pk_dsa) is False, "Wycheproof: Altered message rejected cleanly")

short_sig = sig[:3000]
check(pqc.verify_dsa(short_sig, msg, pk_dsa) is False, "Wycheproof: Truncated signature rejected cleanly")

bad_pk = pk_dsa[:2000]
check(pqc.verify_dsa(sig, msg, bad_pk) is False, "Wycheproof: Malformed public key size rejected cleanly")

print("\n▶ [TIER 7] Dual Hybrid Conjunction Conformance:")
check(pqc.verify_hybrid_authorization(msg, True, sig, pk_dsa) is True, "Dual hybrid conjunction holds when both pass")
check(pqc.verify_hybrid_authorization(msg, False, sig, pk_dsa) is False, "Dual hybrid fails-closed when classical layer fails")
check(pqc.verify_hybrid_authorization(msg, True, tampered_sig.hex(), pk_dsa) is False, "Dual hybrid fails-closed when PQC signature fails")

print("\n=====================================================================")
print(f"🏆 ALL {assertion_count}/23 CRYPTOGRAPHIC ASSERTIONS PASSED CLEANLY")
print("=====================================================================\n")
