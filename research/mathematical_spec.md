# Martin's Algorithm — Mathematical Specification

## 1. Feature Vector

For each crypto asset *i*, define a feature vector **x**_i ∈ [0,1]^9:

| Index | Feature | Source |
|---|---|---|
| 1 | market_activity | CoinMarketCap 24h volume (log-normalized) |
| 2 | liquidity | CMC rank-inverted [0,1] |
| 3 | volume | 24h volume change |
| 4 | onchain_activity | Etherscan/BscScan tx count |
| 5 | developer_activity | GitHub commits (90d) |
| 6 | exchange_activity | Number of trading pairs |
| 7 | project_health | 7d price trend signal |
| 8 | recovery_evidence | Migration/claim mechanism signal |
| 9 | ownership_evidence | Wallet scan match signal |

## 2. Base Score

```
S_i = ∑_j  w_j · x_{ij}

Default weights:
  w = [0.12, 0.12, 0.08, 0.15, 0.10, 0.08, 0.10, 0.15, 0.10]
  ∑w = 1.0
```

## 3. Recovery Probability

```
logit_i = 2.0 · x_{rec} + 1.5 · x_{own} - 2.0 · risk_i

P_rec(i) = σ(logit_i) = 1 / (1 + exp(-logit_i))
```

## 4. Martin Score

```
M_i = α·S_i + β·P_rec(i) + γ·C_i - δ·risk_i

Default hyperparameters:
  α = 0.60   (base feature weight)
  β = 0.25   (recovery probability weight)
  γ = 0.15   (confidence weight)
  δ = 0.50   (risk penalty)

M_i ∈ [0, 1]  (clamped)
```

## 5. Candidate Selection QUBO

**Problem:** Select exactly K assets from N candidates to maximize total Martin Score.

**QUBO formulation:**

```
min_q  C(q) = -∑_i M_i·q_i  +  λ·(∑_i q_i - K)²
subject to  q_i ∈ {0, 1}
```

**QUBO matrix Q (upper triangular):**

```
Q_{ii} = -M_i + λ·(1 - 2K)      (diagonal)
Q_{ij} = 2λ    for i < j         (off-diagonal)
constant = λ·K²
```

## 6. Quantum Extension (Research)

Mapping to Ising variables:
```
q_i = (1 - Z_i) / 2
```

The QUBO maps to an Ising Hamiltonian amenable to QAOA.

**Requirement before claiming quantum advantage:**
Any quantum implementation must be benchmarked against `exact_select`
on the same problem instances, reporting:
- Wall-clock time
- Oracle/data-loading cost
- Circuit depth and shot count
- Noise model
- Solution quality vs. optimal

## 7. Classification Thresholds

| Threshold | Label |
|---|---|
| M_i ≥ 0.65 | ACTIVE |
| 0.40 ≤ M_i < 0.65 | WEAK |
| 0.20 ≤ M_i < 0.40 | DORMANT |
| M_i < 0.20, liq=0, dev=0 | DEAD / ABANDONED |
| recovery_evidence ≥ 0.60 + ownership ≥ 0.30 | RECOVERABLE |
| migration_evidence ≥ 0.70 | MIGRATED |
| confidence < 0.15 | UNKNOWN |
