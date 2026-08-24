import numpy as np
class QUBOOptimizer:
    def __init__(self, max_k: int = 2): self.max_k = max_k
    def solve_classical(self, candidates):
        if not candidates or len(candidates) <= self.max_k: return candidates
        scores = np.array([c.get('martin_score', 0) for c in candidates])
        return [candidates[i] for i in np.argsort(-scores)[:self.max_k]]
