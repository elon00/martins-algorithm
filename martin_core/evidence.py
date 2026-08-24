"""Evidence root engine with deterministic Merkle tree."""

import hashlib
import json
from typing import Any


class EvidenceEngine:
    """Computes cryptographic evidence roots for ZK verification."""

    @staticmethod
    def build_evidence_root(signals: list[dict[str, Any]]) -> str:
        """Constructs a binary SHA-256 Merkle root from signal dictionaries."""
        if not signals:
            return hashlib.sha256(b"EMPTY").hexdigest()
        hashes = [
            hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
            for s in signals
        ]
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            hashes = [
                hashlib.sha256((hashes[i] + hashes[i + 1]).encode()).hexdigest()
                for i in range(0, len(hashes), 2)
            ]
        return hashes[0]
