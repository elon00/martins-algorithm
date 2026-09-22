# Security Policy

## Scope

Martin's Algorithm is research/prototype software. It should not be used as an unattended custody, recovery, trading, or transaction-execution system.

## Reporting

Report sensitive vulnerabilities privately through GitHub security reporting when available. Do not post:

- private keys or seed phrases
- API tokens
- wallet credentials
- exploitable transaction details
- personal or financial data

Include the affected commit, reproduction steps, impact, and suggested mitigation where possible.

## High-risk boundaries

Changes affecting these areas require extra review:

- transaction or wallet execution
- authorization/policy logic
- ML-DSA / ML-KEM bridge code
- API authentication
- external chain data ingestion
- automatic action based on scoring

## Safe defaults

Production-like deployments must keep human approval enabled and automatic transaction value disabled unless a separately reviewed execution policy explicitly changes that behavior.

## Cryptography

Use of standardized primitives does not imply that this application is FIPS-validated or independently audited.
