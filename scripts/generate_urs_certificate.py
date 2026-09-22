#!/usr/bin/env python3
"""Generate a repository-internal signed evidence report.

The report runs the checked-in verification commands, records their success,
hashes a JSON payload, and signs that payload with the repository's ML-DSA
integration. It is NOT an independent certificate, FIPS validation, security
audit, production-readiness decision, or legal/compliance approval.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.pqc_engine import PQCEngine


def run(command: list[str], title: str) -> None:
    print(f"▶ {title}...")
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        print(f"  FAILED: {title}")
        print(proc.stderr or proc.stdout)
        raise SystemExit(proc.returncode)
    print(f"  PASS: {title}")


print("MARTIN'S ALGORITHM — GENERATING INTERNAL EVIDENCE REPORT")

run([sys.executable, "tests/test_nist_pqc.py"], "[1/4] PQC integration/adversarial tests")
run([sys.executable, "scripts/audit_crypto.py"], "[2/4] Cryptographic integration audit")
run([sys.executable, "scripts/reality_universal.py"], "[3/4] Repository-defined internal gates")
run([sys.executable, "main.py"], "[4/4] Prototype pipeline smoke test")

pqc = PQCEngine()
reporter_seed = (b"\x77" * 32).hex()
reporter_pk, reporter_sk = pqc.generate_dsa_keypair(reporter_seed)

report_payload = {
    "protocol": "MartinsAlgorithm",
    "reportType": "REPOSITORY_INTERNAL_EVIDENCE",
    "generatedAt": datetime.now(timezone.utc).isoformat(),
    "status": "INTERNAL_CHECKS_COMPLETED",
    "scope": {
        "quantumLayer": "SIMULATED_QUANTUM_ANNEALING_SQA_QUBO",
        "cryptography": "APPLICATION_LAYER_ML_KEM_768_AND_ML_DSA_65_INTEGRATION",
        "assetExecution": "DISABLED_BY_DEFAULT_AND_HUMAN_GATED",
    },
    "limitations": {
        "independentVerification": False,
        "externalSecurityAudit": False,
        "fipsModuleValidation": False,
        "productionCertification": False,
        "legalOrRegulatoryApproval": False,
        "realQuantumHardwareClaimed": False,
    },
    "checks": [
        "PQC integration and adversarial tests",
        "cryptographic integration audit",
        "repository-defined internal gates",
        "prototype pipeline smoke test",
    ],
    "reporter": {
        "scheme": "ML-DSA-65 integration",
        "publicKeyHex": reporter_pk,
        "note": "This signature authenticates this repository-generated report; it does not make the report independent.",
    },
}

canonical = json.dumps(report_payload, sort_keys=True, separators=(",", ":"))
master_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
signature = pqc.sign_dsa(canonical, reporter_sk)

final_report = {
    **report_payload,
    "sha256": master_hash,
    "signatureHex": signature,
}

os.makedirs("reality", exist_ok=True)
os.makedirs("docs/reality", exist_ok=True)

json_path = "reality/URS_EVIDENCE_CERTIFICATE.json"
md_path = "docs/reality/URS_EVIDENCE_CERTIFICATE.md"

with open(json_path, "w", encoding="utf-8") as handle:
    json.dump(final_report, handle, indent=2)

markdown = f"""# Martin's Algorithm — Internal Evidence Report

Generated: `{final_report["generatedAt"]}`  
SHA-256: `{master_hash}`  
ML-DSA signature bytes: `{len(signature) // 2}`

## Checks executed

- PQC integration and adversarial tests
- cryptographic integration audit
- repository-defined internal gates
- prototype pipeline smoke test

## Interpretation

This file is generated and signed by the repository itself. It is useful for
regression tracking and reproducibility, but it is **not**:

- an independent security audit;
- a FIPS validation of the application;
- a production-readiness certificate;
- a legal or regulatory approval;
- evidence of real quantum-hardware execution;
- authorization to access or recover third-party assets.

The signature authenticates the generated report only.
"""

with open(md_path, "w", encoding="utf-8") as handle:
    handle.write(markdown)

print("Internal evidence report generated")
print(f"  SHA-256: {master_hash}")
print(f"  JSON:    {json_path}")
print(f"  Markdown:{md_path}")
print("  Independent verification: NOT CLAIMED")
