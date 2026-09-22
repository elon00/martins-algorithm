import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from martin_core.scoring import MartinScoringEngine
from martin_core.evidence import EvidenceEngine
from quantum.qubo_optimizer import QUBOOptimizer
from security.policy_engine import PolicyEngine
from security.pqc_engine import PQCEngine

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
    
    # 2. Generate NIST FIPS 204 ML-DSA-65 Post-Quantum Agent Keys
    pk, sk = pqc.generate_dsa_keypair()
    auth_msg = f"{opt['project']}:{opt['evidence_root']}:{opt['martin_score']}"
    pqc_sig = pqc.sign_dsa(auth_msg, sk)
    
    # 3. Dual Hybrid Security Gate Evaluation
    decision = policy.evaluate(
        opt,
        dsa_signature_hex=pqc_sig,
        dsa_public_key_hex=pk,
        classical_signature_valid=True
    )
    
    print(f"[🎯] Optimized Selection: {[c['project'] for c in selected]}")
    print(f"[⚛️] SQA Ground Energy:    {sqa_result['energy']:.2f}")
    print(f"[📊] Martin Score:         {opt['martin_score']} / 100")
    print(f"[🔒] ZK Evidence Root:     {opt['evidence_root'][:16]}... (Committed)")
    print(f"[🛡️] PQC Scheme:           NIST FIPS 204 ML-DSA-65 (1952B pk, 3309B sig)")
    print(f"[✅] Policy Gate:          {decision['action']}")
    print(f"[📜] Security Status:      {decision['reason']}")
    print("\nRESEARCH PROTOTYPE PIPELINE COMPLETED. Internal checks are not production certification.\n")

if __name__ == "__main__":
    run()
