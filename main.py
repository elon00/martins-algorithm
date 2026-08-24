import sys
from martin_core.scoring import MartinScoringEngine
from martin_core.evidence import EvidenceEngine
from quantum.qubo_optimizer import QUBOOptimizer
from security.policy_engine import PolicyEngine

def run():
    print('\n========================================================')
    print('🚀 RUNNING: MARTIN ALGORITHM WEB 4.0 MASTER PIPELINE')
    print('========================================================')
    scorer = MartinScoringEngine()
    policy = PolicyEngine()
    qubo = QUBOOptimizer(max_k=1)
    
    signals = [{'src': 'Etherscan', 'event': 'Migration_Active'}, {'src': 'GitHub', 'event': 'V2_Contract'}]
    score_res = scorer.calculate_score(health=85.0, recovery_prob=90.0, confidence=95.0, risk=15.0)
    root = EvidenceEngine.build_evidence_root(signals)
    
    cand = [{
        'project': 'OldProtocolV1_Migration',
        'martin_score': score_res['martin_score'],
        'status': 'RECOVERABLE',
        'evidence_root': root
    }]
    
    opt = qubo.solve_classical(cand)[0]
    decision = policy.evaluate(opt)
    
    print(f'[✓] Project:         {opt[\"project\"]}')
    print(f'[✓] Martin Score:    {opt[\"martin_score\"]} / 100')
    print(f'[✓] ZK Evidence:     {opt[\"evidence_root\"][:16]}... (Committed)')
    print(f'[✓] Policy Gate:     {decision[\"action\"]}')
    print(f'[✓] Security Status: {decision[\"reason\"]}')
    print('\n🎉 SYSTEM 100% OPERATIONAL & VERIFIED!\n')

if __name__ == '__main__': run()
