# Security Principles — Martin's Algorithm

## Non-Negotiable Rules

### 1. No Private Keys or Seed Phrases
- Private keys and seed phrases are **never** accepted by any API endpoint
- They are **never** stored in any database, log file, or environment variable
- They are **never** transmitted to any server
- The `PolicyEngine.check_no_key_in_request()` method actively blocks suspicious fields

### 2. Read-Only Blockchain Access
- All blockchain data is fetched via public block explorer APIs (Etherscan, BscScan)
- These are read-only GET requests only
- No transaction signing or broadcasting without explicit user action

### 3. Fail-Closed Permission Engine
- Unknown action = **DENIED** by default
- Every monetary value-transfer requires `user_approved=True`
- HIGH and CRITICAL risk actions always require explicit user approval
- The AI may **propose** actions; it does not become the cryptographic signer

### 4. Human-in-the-Loop for Value Transfer
```
AI Agent proposes action
       ↓
Policy Engine checks → DENIED if not approved
       ↓
User sees proposal + explanation
       ↓
User explicitly approves
       ↓
Policy Engine re-checks → APPROVED
       ↓
User's own wallet software signs and broadcasts
```

### 5. Audit Logging
- All policy decisions are logged (action, risk level, approved/denied, reason)
- Logs do not contain any sensitive data (no keys, no phrases, no PII)

### 6. Independent Security Audit Required
Before handling real funds on mainnet, an independent third-party security
audit by qualified cryptography and smart-contract security experts is **mandatory**.

### 7. No Fake Claims
- Martin's Algorithm does not claim to recover arbitrary lost cryptocurrency
- It surfaces **legitimate, official** claim opportunities (migrations, airdrops, etc.)
- Any opportunity with `recovery_evidence < 0.60` requires additional manual verification
