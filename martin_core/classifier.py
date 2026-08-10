"""
Asset Classifier
================
Labels each crypto asset with a status based on its Martin Score
and raw feature data.

Labels:
    ACTIVE      — Healthy, trading, active project
    WEAK        — Low activity, at-risk
    DORMANT     — No trades/commits in 6+ months
    DEAD        — Zero liquidity, abandoned
    MIGRATED    — Token moved to new contract
    REBRANDED   — Project renamed/restructured
    RECOVERABLE — Official claim/airdrop mechanism exists
    ABANDONED   — Team gone, no recovery path
    UNKNOWN     — Insufficient data
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .scoring import Candidate, martin_score


class AssetStatus(str, Enum):
    ACTIVE      = "ACTIVE"
    WEAK        = "WEAK"
    DORMANT     = "DORMANT"
    DEAD        = "DEAD"
    MIGRATED    = "MIGRATED"
    REBRANDED   = "REBRANDED"
    RECOVERABLE = "RECOVERABLE"
    ABANDONED   = "ABANDONED"
    UNKNOWN     = "UNKNOWN"


@dataclass(frozen=True)
class ClassificationResult:
    asset_id: str
    status: AssetStatus
    martin_score: float
    recovery_probability: float
    explanation: str


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

ACTIVE_THRESHOLD      = 0.65
WEAK_THRESHOLD        = 0.40
DORMANT_THRESHOLD     = 0.20
RECOVERABLE_EVIDENCE  = 0.60  # minimum recovery_evidence to label RECOVERABLE
MIGRATION_EVIDENCE    = 0.70  # minimum migration_evidence signal
CONFIDENCE_MIN        = 0.15  # below this = UNKNOWN


def classify(candidate: Candidate) -> ClassificationResult:
    """
    Classify a crypto asset based on its features and Martin Score.

    Classification priority (top = wins):
      1. UNKNOWN       — too little data
      2. RECOVERABLE   — strong recovery evidence regardless of score
      3. MIGRATED      — migration signal detected
      4. REBRANDED     — rebranded signal detected
      5. ACTIVE        — high score
      6. WEAK          — medium score
      7. DORMANT       — low score, some signal
      8. DEAD          — very low score, no signal
      9. ABANDONED     — dead + no recovery path
    """
    score = martin_score(candidate)
    features = candidate.features

    rec_ev  = float(features.get("recovery_evidence",  0.0))
    mig_ev  = float(features.get("migration_evidence", 0.0))
    reb_ev  = float(features.get("rebrand_evidence",   0.0))
    liq     = float(features.get("liquidity",          0.0))
    dev_act = float(features.get("developer_activity", 0.0))
    own_ev  = float(features.get("ownership_evidence", 0.0))
    conf    = candidate.confidence

    # 1. UNKNOWN
    if conf < CONFIDENCE_MIN:
        return ClassificationResult(
            asset_id=candidate.asset_id,
            status=AssetStatus.UNKNOWN,
            martin_score=score,
            recovery_probability=rec_ev,
            explanation="Insufficient data to classify this asset.",
        )

    # 2. RECOVERABLE — strong recovery signal
    if rec_ev >= RECOVERABLE_EVIDENCE and own_ev >= 0.30:
        return ClassificationResult(
            asset_id=candidate.asset_id,
            status=AssetStatus.RECOVERABLE,
            martin_score=score,
            recovery_probability=rec_ev,
            explanation=(
                f"Official recovery/claim mechanism likely exists "
                f"(recovery_evidence={rec_ev:.2f}, ownership_evidence={own_ev:.2f})."
            ),
        )

    # 3. MIGRATED
    if mig_ev >= MIGRATION_EVIDENCE:
        return ClassificationResult(
            asset_id=candidate.asset_id,
            status=AssetStatus.MIGRATED,
            martin_score=score,
            recovery_probability=rec_ev,
            explanation=f"Token appears to have migrated to a new contract (migration_evidence={mig_ev:.2f}).",
        )

    # 4. REBRANDED
    if reb_ev >= 0.65:
        return ClassificationResult(
            asset_id=candidate.asset_id,
            status=AssetStatus.REBRANDED,
            martin_score=score,
            recovery_probability=rec_ev,
            explanation=f"Project may have rebranded (rebrand_evidence={reb_ev:.2f}).",
        )

    # 5-9: Score-based classification
    if score >= ACTIVE_THRESHOLD:
        status = AssetStatus.ACTIVE
        explanation = f"Healthy asset with Martin Score {score:.3f}."
    elif score >= WEAK_THRESHOLD:
        status = AssetStatus.WEAK
        explanation = f"At-risk asset — declining activity (score={score:.3f})."
    elif liq < 0.05 and dev_act < 0.05:
        # Completely dead
        if rec_ev < 0.10:
            status = AssetStatus.ABANDONED
            explanation = "No liquidity, no developer activity, no recovery path found."
        else:
            status = AssetStatus.DEAD
            explanation = "Zero liquidity and no active development."
    elif score >= DORMANT_THRESHOLD:
        status = AssetStatus.DORMANT
        explanation = f"Asset is dormant — no significant activity in 6+ months (score={score:.3f})."
    else:
        status = AssetStatus.DEAD
        explanation = f"Asset appears dead — very low score ({score:.3f}) and minimal signal."

    return ClassificationResult(
        asset_id=candidate.asset_id,
        status=status,
        martin_score=score,
        recovery_probability=rec_ev,
        explanation=explanation,
    )


def batch_classify(candidates: list[Candidate]) -> list[ClassificationResult]:
    """Classify a list of candidates and return results sorted by Martin Score descending."""
    results = [classify(c) for c in candidates]
    results.sort(key=lambda r: r.martin_score, reverse=True)
    return results
