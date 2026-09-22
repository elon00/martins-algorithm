# Martin's Algorithm

Evidence-oriented research software for **crypto-asset opportunity scoring, simulated quantum annealing (SQA/QUBO), post-quantum authorization experiments, and human-gated decision support**.

## Status

**RESEARCH / PROTOTYPE — NOT AN AUTONOMOUS ASSET-RECOVERY OR TRADING SYSTEM**

The repository contains working scoring, evidence, SQA/QUBO, policy, and ML-DSA/ML-KEM integration code. It does not establish ownership of assets, legal entitlement to recover funds, guaranteed profitability, production custody safety, or independently audited cryptographic security.

### Evidenced in this repository

- deterministic scoring and evidence-root generation
- simulated quantum annealing / QUBO optimization experiments
- application-layer ML-KEM-768 and ML-DSA-65 integration via the checked-in Node bridge
- positive and adversarial/tamper tests
- fail-closed hybrid authorization logic
- default environment policy that disables automatic transaction value and requires human approval

### Not claimed

- real asset recovery authority or custody
- automatic movement of third-party funds
- investment advice or guaranteed opportunity detection
- independent security or cryptographic audit
- FIPS validation of the application as a cryptographic module
- real quantum-hardware execution
- zero-knowledge proof implementation merely because a hash commitment exists
- production readiness solely from internal “reality” gates

## Safe operating defaults

The sample environment intentionally uses:

```env
MARTIN_MAX_TRANSACTION_VALUE=0
MARTIN_REQUIRE_USER_APPROVAL=true
```

Keep those defaults unless a separately reviewed execution layer is added. Do not use this software to access or move assets without authorization.

## Quick start

Requirements:

- Python 3.11+
- Node.js 22+
- npm

```bash
git clone https://github.com/elon00/martins-algorithm.git
cd martins-algorithm

python -m pip install -r requirements.txt -r requirements-dev.txt
npm ci

ruff check .
pytest
npm test
```

## Verification

Useful checks:

```bash
python tests/test_nist_pqc.py
python scripts/audit_crypto.py
python scripts/reality_universal.py
python main.py
```

Repository-defined scorecards are internal engineering artifacts. They prove only the checks they execute.

## Architecture

- `martin_core/` — scoring and evidence logic
- `quantum/` — simulated quantum annealing / QUBO research
- `security/` — authorization policy and PQC bridge
- `martin_api/` — API surface
- `agents/` — orchestration experiments
- `tests/` — automated verification
- `scripts/` — audit/reality helpers

## Security and responsible use

See [SECURITY.md](SECURITY.md).

Never commit private keys, seed phrases, API tokens, wallet credentials, or user asset data. Any future execution layer should require explicit authorization, transaction simulation, policy limits, signing separation, audit logging, and human approval by default.

## Production boundary

Before describing this system as production-ready, require at minimum:

1. independent security and cryptographic review;
2. pinned/reproducible Python dependencies and vulnerability scanning;
3. authenticated/authorized APIs;
4. secrets management and key isolation;
5. threat model and abuse-case testing;
6. transaction simulation plus explicit human approval;
7. monitoring, audit logs, rollback and incident response;
8. legal/compliance review for any asset-recovery or financial workflow.

## License

ISC, as declared in `package.json`, unless/until the repository license is intentionally changed.
