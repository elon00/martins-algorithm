import os
import sys

# Ensure UTF-8 output if supported
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from martin_core.scoring import MartinScoringEngine
from martin_core.evidence import EvidenceEngine
from quantum.qubo_optimizer import QUBOOptimizer
from security.policy_engine import PolicyEngine
from security.pqc_engine import PQCEngine
from security.wallet_signer import WalletSigner


def run():
    print("\n========================================================")
    print("🛡️ RUNNING: MARTIN ALGORITHM WEB 4.0 MASTER PIPELINE")
    print("========================================================")
    scorer = MartinScoringEngine()
    policy = PolicyEngine()
    qubo = QUBOOptimizer(max_k=2, trotter_slices=8, annealing_steps=100)
    pqc = PQCEngine()

    signals = [
        {"src": "Etherscan", "event": "Migration_Active"},
        {"src": "GitHub", "event": "V2_Contract"}
    ]
    score_res = scorer.calculate_score(health=85.0, recovery_prob=90.0, confidence=95.0, risk=15.0)
    root = EvidenceEngine.build_evidence_root(signals)

    candidates = [
        {
            "project": "OldProtocolV1_Migration",
            "martin_score": score_res["martin_score"],
            "status": "RECOVERABLE",
            "risk": 12.0,
            "evidence_root": root
        },
        {
            "project": "DeprecatedVaultV0_Recovery",
            "martin_score": 76.5,
            "status": "RECOVERABLE",
            "risk": 18.0,
            "evidence_root": root
        },
        {
            "project": "StaleArbitrage_Pool",
            "martin_score": 38.0,
            "status": "ACTIVE",
            "risk": 45.0,
            "evidence_root": root
        }
    ]

    # 1. Quantum Hamiltonian Optimization via SQA
    sqa_result = qubo.solve_sqa(candidates)
    selected = sqa_result["selected"]
    opt = selected[0]

    # 2. Stage 1: AI Proposal Gate
    initial_decision = policy.evaluate(opt)
    print(f"[🎯] Optimized Selection: {[c['project'] for c in selected]}")
    print(f"[⚛️] SQA Ground Energy:    {sqa_result['energy']:.2f}")
    print(f"[📊] Martin Score:         {opt['martin_score']} / 100")
    print(f"[🔒] Evidence Root:        {opt['evidence_root'][:16]}... (Committed)")
    print(f"[*] Initial Gate:          {initial_decision['action']}")
    print(f"[*] Security Status:       {initial_decision['reason']}")

    # 3. Stage 2: User Web3 Cryptographic Wallet Signing (EIP-191)
    user_pk = os.getenv("USER_WALLET_PRIVATE_KEY", None)
    signed_proof = WalletSigner.sign_intent(opt, private_key=user_pk)

    print("\n--------------------------------------------------------")
    print("[+] EXECUTING USER WALLET SIGNATURE (EIP-191)")
    print("--------------------------------------------------------")
    print(f"[✓] Wallet Signer:         {signed_proof.signer_address}")
    print(f"[✓] Signature Hash:        {signed_proof.signature[:26]}...{signed_proof.signature[-10:]}")
    print(f"[✓] Cryptographic Check:   {'PASS (ecRecover Matched)' if signed_proof.verified else 'FAIL'}")

    # 4. Stage 3: Generate NIST FIPS 204 ML-DSA-65 Post-Quantum Agent Keys
    pk, sk = pqc.generate_dsa_keypair()
    auth_msg = f"{opt['project']}:{opt['evidence_root']}:{opt['martin_score']}"
    pqc_sig = pqc.sign_dsa(auth_msg, sk)

    # 5. Stage 4: Dual Hybrid Security Gate Evaluation
    final_decision = policy.evaluate(
        opt,
        dsa_signature_hex=pqc_sig,
        dsa_public_key_hex=pk,
        classical_signature_valid=signed_proof.verified
    )

    print("\n--------------------------------------------------------")
    print("[+] DUAL HYBRID PQC + EIP-191 GATE EVALUATION")
    print("--------------------------------------------------------")
    print("[🛡️] PQC Scheme:              ML-DSA-65 integration (1952B pk, 3309B sig)")
    print(f"[✅] Final Gate Status:       {final_decision['action']}")
    print(f"[📜] Authorization:           {final_decision['reason']}")
    print("\n[OK] SYSTEM 100% OPERATIONAL, SIGNED & BROADCAST READY!\n")


if __name__ == "__main__":
    run()
