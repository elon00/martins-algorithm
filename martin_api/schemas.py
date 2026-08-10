"""
Pydantic Schemas — Martin's Algorithm API
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Asset schemas
# ---------------------------------------------------------------------------

class AssetIn(BaseModel):
    asset_id: str = Field(..., description="Unique asset identifier, e.g. 'cmc:1:BTC'")
    features: dict[str, float] = Field(
        default_factory=dict,
        description="Feature scores in [0,1]. Keys: market_activity, liquidity, volume, "
                    "onchain_activity, developer_activity, exchange_activity, "
                    "project_health, recovery_evidence, ownership_evidence",
    )
    risk: float = Field(0.0, ge=0.0, le=1.0, description="Risk score [0,1]")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Data confidence [0,1]")


class AssetScoreOut(BaseModel):
    asset_id: str
    martin_score: float
    recovery_probability: float


class AssetClassifyOut(BaseModel):
    asset_id: str
    status: str
    martin_score: float
    recovery_probability: float
    explanation: str


# ---------------------------------------------------------------------------
# Rank / Optimize
# ---------------------------------------------------------------------------

class RankRequest(BaseModel):
    assets: list[AssetIn] = Field(..., min_length=1)
    top_k: int = Field(10, ge=1, le=500)


class RankOut(BaseModel):
    results: list[AssetScoreOut]
    total: int


class OptimizeRequest(BaseModel):
    assets: list[AssetIn] = Field(..., min_length=1)
    k: int = Field(1, ge=1, le=100)
    penalty: float = Field(2.0, ge=0.01)


class OptimizeOut(BaseModel):
    selected_asset_ids: list[str]
    objective: float
    solver: str
    n_candidates: int
    k: int


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    pages: int = Field(3, ge=1, le=50)
    page_size: int = Field(100, ge=10, le=200)
    top_k_opportunities: int = Field(30, ge=1, le=200)


class OpportunityOut(BaseModel):
    asset_id: str
    status: str
    martin_score: float
    recovery_probability: float
    explanation: str


class ScanOut(BaseModel):
    scan_id: str
    timestamp: float
    total_scanned: int
    opportunities: list[OpportunityOut]
    errors: list[str]


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

class PolicyCheckRequest(BaseModel):
    action: str
    asset_id: str | None = None
    value: float = Field(0.0, ge=0.0)
    risk_level: str = Field("read_only")
    user_approved: bool = False


class PolicyCheckOut(BaseModel):
    approved: bool
    reason: str
    risk_level: str
    action: str
