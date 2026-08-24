from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class MartinWeights:
    alpha: float = 0.60
    beta: float = 0.25
    gamma: float = 0.15
    delta: float = 0.50

class MartinScoringEngine:
    def __init__(self, weights: MartinWeights = MartinWeights()):
        self.weights = weights
        self.version = "martin-v2.0"

    def calculate_score(self, health: float, recovery_prob: float, confidence: float, risk: float) -> Dict[str, Any]:
        s, p, c, r = max(0.0, min(100.0, health)), max(0.0, min(100.0, recovery_prob)), max(0.0, min(100.0, confidence)), max(0.0, min(100.0, risk))
        score = max(0.0, min(100.0, round(self.weights.alpha * s + self.weights.beta * p + self.weights.gamma * c - self.weights.delta * r, 4)))
        return {"algorithm_version": self.version, "martin_score": score}
