# 🧠 Martin's Algorithm v1.0
### *Crypto Asset Recovery & Opportunity Detection Engine (CARI)*

[![CI](https://github.com/elon00/luther-algorithm/actions/workflows/ci.yml/badge.svg)](https://github.com/elon00/luther-algorithm/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com)

---

## What is Martin's Algorithm?

**Martin's Algorithm** is a permissioned, hybrid classical-quantum **Crypto Asset Recovery & Opportunity Detection Engine**.

It scans the entire CoinMarketCap universe (5000+ coins), detects **dormant, migrated, dead, and recoverable** crypto assets, scores each using a mathematically rigorous formula, and surfaces legitimate claim opportunities — all with a **fail-closed permission engine** that never stores your private keys or seed phrases.

```
CoinMarketCap API  +  Blockchain APIs
          ↓
   Martin Scoring Engine
   M_i = α·S + β·P_rec + γ·C − δ·Risk
          ↓
   Dead / Dormant / Recoverable Classifier
          ↓
   QUBO → Classical Optimizer (quantum-ready)
          ↓
   Fail-Closed Permission Engine
          ↓
   User Approval Gate  ← seed phrase NEVER stored
          ↓
   Opportunity Dashboard + REST API
```

---

## Architecture

```
martins-algorithm/
├── martin_core/         ← Scoring, QUBO, Optimizer, Policy Engine
├── data/                ← CoinMarketCap, Blockchain, GitHub adapters
├── agents/              ← Autonomous scanner & recovery agents
├── martin_api/          ← FastAPI REST backend
├── dashboard/           ← Premium HTML/CSS/JS live dashboard
├── security/            ← Audit log, principles
├── research/            ← Whitepaper, mathematical spec, quantum model
└── tests/               ← Full pytest test suite
```

---

## Martin Score Formula

For each crypto asset *i*:

```
M_i = α · S_i  +  β · P_rec(i)  +  γ · C_i  −  δ · Risk_i

where:
  S_i     = weighted feature score (market, liquidity, on-chain, dev, community)
  P_rec   = sigmoid( θ₀ + θᵀ·z_i )  — recovery probability
  C_i     = confidence score [0,1]
  Risk_i  = normalized risk factor [0,1]
  α=0.60, β=0.25, γ=0.15, δ=0.50
```

**Candidate Selection (QUBO):**
```
min_q  [ −∑ M_i·q_i  +  λ·(∑q_i − K)² ]
subject to  q_i ∈ {0,1}
```

---

## Asset Classification

| Label | Meaning |
|---|---|
| `ACTIVE` | Healthy, trading, active project |
| `WEAK` | Low activity, at-risk |
| `DORMANT` | No trades/commits in 6+ months |
| `DEAD` | Zero liquidity, abandoned |
| `MIGRATED` | Token moved to new contract |
| `REBRANDED` | Project renamed/restructured |
| `RECOVERABLE` | Official claim/airdrop mechanism exists |
| `ABANDONED` | Team gone, no recovery path |
| `UNKNOWN` | Insufficient data |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/elon00/luther-algorithm.git
cd luther-algorithm

# 2. Virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Add your CoinMarketCap API key to .env

# 5. Run API
uvicorn martin_api.main:app --reload

# 6. Open API docs
# http://localhost:8000/docs

# 7. Open Dashboard
# Open dashboard/index.html in your browser
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/score` | Score a single asset |
| `POST` | `/rank` | Rank multiple assets |
| `POST` | `/classify` | Classify asset status |
| `POST` | `/scan` | Trigger a CMC scan |
| `GET` | `/opportunities` | List top recovery opportunities |
| `POST` | `/optimize/classical` | QUBO classical optimizer |

Full interactive docs: `http://localhost:8000/docs`

---

## Security Principles

> ⛔ **Private keys and seed phrases are NEVER stored, logged, transmitted, or requested.**

- All blockchain reads are **read-only** (Etherscan/BscScan public APIs)
- Every value-transfer action requires **explicit user approval**
- AI agents **propose** actions — cryptographic signing stays with you
- Fail-closed `PolicyEngine`: unknown = denied
- No hard-coded credentials anywhere in source code

---

## Run Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## Project Roadmap

- [x] Martin Score Engine
- [x] Dead/Dormant/Recoverable Classifier
- [x] QUBO + Classical Optimizer
- [x] Fail-closed Permission Engine
- [x] FastAPI REST Backend
- [x] Live Dashboard
- [x] CoinMarketCap Adapter
- [x] Blockchain Read Adapter (Etherscan)
- [x] GitHub Activity Agent
- [x] CI/CD (GitHub Actions)
- [ ] QAOA Quantum Module (research milestone)
- [ ] Multisig + Timelock (v2)
- [ ] 500-Agent Fabric (v2)
- [ ] Post-Quantum Cryptography layer (v3)

---

## Research

- [Mathematical Specification](research/mathematical_spec.md)
- [Quantum Model](research/quantum_model.md)
- [Whitepaper](research/whitepaper.md)
- [Security Principles](security/principles.md)

---

## License

MIT License — Copyright © 2026 Martin's Algorithm Contributors

---

## Disclaimer

This is a research and opportunity-detection platform. It does not guarantee profits.
No seed phrases or private keys are requested or stored. Independent security and legal
review is mandatory before handling real funds on mainnet.
