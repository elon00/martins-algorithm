"""
Martin's Algorithm — FastAPI Application
=========================================
REST API for scoring, classifying, ranking, and scanning crypto assets.

Run:
    uvicorn martin_api.main:app --reload
    → http://localhost:8000/docs
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data.coinmarketcap import CoinMarketCapAdapter
from martin_core.classifier import batch_classify, classify
from martin_core.optimizer import select
from martin_core.policy import ActionRequest, PolicyEngine, RiskLevel
from martin_core.scoring import Candidate, martin_score, rank_candidates
from martin_core.scoring import recovery_probability

from .schemas import (
    AssetIn,
    AssetClassifyOut,
    AssetScoreOut,
    OptimizeOut,
    OptimizeRequest,
    OpportunityOut,
    PolicyCheckOut,
    PolicyCheckRequest,
    RankOut,
    RankRequest,
    ScanOut,
    ScanRequest,
)

# ---------------------------------------------------------------------------
# Startup / teardown
# ---------------------------------------------------------------------------

_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["policy"] = PolicyEngine()
    _state["cmc"] = CoinMarketCapAdapter()
    _state["start_time"] = time.time()
    yield
    _state.clear()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Martin's Algorithm API",
    description=(
        "Crypto Asset Recovery & Opportunity Detection Engine (CARI). "
        "Score, classify, rank, and discover recovery opportunities for crypto assets."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_candidate(a: AssetIn) -> Candidate:
    return Candidate(
        asset_id=a.asset_id,
        features=dict(a.features),
        risk=a.risk,
        confidence=a.confidence,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health():
    """Service health check."""
    uptime = time.time() - _state.get("start_time", time.time())
    return {
        "status": "ok",
        "service": "martin-algorithm",
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 1),
    }


@app.post("/score", response_model=AssetScoreOut, tags=["Scoring"])
def score_asset(asset: AssetIn):
    """Compute the Martin Score for a single asset."""
    c = _to_candidate(asset)
    return AssetScoreOut(
        asset_id=asset.asset_id,
        martin_score=martin_score(c),
        recovery_probability=recovery_probability(c),
    )


@app.post("/classify", response_model=AssetClassifyOut, tags=["Classification"])
def classify_asset(asset: AssetIn):
    """Classify a single asset's status (ACTIVE, DORMANT, RECOVERABLE, etc.)."""
    c = _to_candidate(asset)
    result = classify(c)
    return AssetClassifyOut(
        asset_id=result.asset_id,
        status=result.status.value,
        martin_score=result.martin_score,
        recovery_probability=result.recovery_probability,
        explanation=result.explanation,
    )


@app.post("/rank", response_model=RankOut, tags=["Scoring"])
def rank_assets(req: RankRequest):
    """Score and rank a list of assets by Martin Score (descending)."""
    candidates = [_to_candidate(a) for a in req.assets]
    ranked = rank_candidates(candidates, top_k=req.top_k)
    return RankOut(
        results=[
            AssetScoreOut(
                asset_id=c.asset_id,
                martin_score=s,
                recovery_probability=recovery_probability(c),
            )
            for c, s in ranked
        ],
        total=len(ranked),
    )


@app.post("/optimize/classical", response_model=OptimizeOut, tags=["Optimization"])
def optimize_classical(req: OptimizeRequest):
    """
    Select the optimal K assets from a candidate list using the classical QUBO solver.
    For N > 20 this uses the greedy approximation; for N <= 20 it is exact.
    """
    if req.k > len(req.assets):
        raise HTTPException(
            status_code=400,
            detail=f"k={req.k} cannot exceed number of assets ({len(req.assets)}).",
        )
    candidates = [_to_candidate(a) for a in req.assets]
    result = select(candidates, req.k, req.penalty)
    return OptimizeOut(
        selected_asset_ids=result.asset_ids,
        objective=result.objective,
        solver=result.solver,
        n_candidates=result.n_candidates,
        k=result.k,
    )


@app.post("/scan", response_model=ScanOut, tags=["Scan"])
def scan_coinmarketcap(req: ScanRequest):
    """
    Trigger a live CoinMarketCap scan and return recovery opportunities.
    Requires CMC_API_KEY to be set in .env.
    """
    from agents.scanner_agent import ScannerAgent
    agent = ScannerAgent(
        cmc_adapter=_state["cmc"],
        pages=req.pages,
        page_size=req.page_size,
    )
    try:
        result = agent.scan_once(top_k_opportunities=req.top_k_opportunities)
    except (ValueError, KeyError, TypeError, PermissionError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return ScanOut(
        scan_id=result.scan_id,
        timestamp=result.timestamp,
        total_scanned=result.total_scanned,
        opportunities=[
            OpportunityOut(
                asset_id=r.asset_id,
                status=r.status.value,
                martin_score=r.martin_score,
                recovery_probability=r.recovery_probability,
                explanation=r.explanation,
            )
            for r in result.opportunities
        ],
        errors=result.errors,
    )


@app.get("/opportunities", response_model=list[OpportunityOut], tags=["Scan"])
def get_opportunities():
    """
    Return a curated list of example recovery opportunities.
    Run /scan first to populate with live data.
    """
    # Demo data — replace with persistent storage in production
    return [
        OpportunityOut(
            asset_id="demo:example:TOK",
            status="RECOVERABLE",
            martin_score=0.72,
            recovery_probability=0.68,
            explanation="Example: Token has an official migration claim page.",
        )
    ]


@app.post("/policy/check", response_model=PolicyCheckOut, tags=["Security"])
def check_policy(req: PolicyCheckRequest):
    """
    Run a policy check for a proposed action without executing it.
    Use this to verify if an action would be permitted before submitting.
    """
    engine: PolicyEngine = _state["policy"]

    # Map string risk level to enum
    try:
        risk = RiskLevel(req.risk_level.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid risk_level: '{req.risk_level}'. "
                   f"Valid values: {[r.value for r in RiskLevel]}",
        )

    action_req = ActionRequest(
        action=req.action,
        asset_id=req.asset_id,
        value=req.value,
        risk=risk,
        user_approved=req.user_approved,
    )
    decision = engine.authorize(action_req)

    return PolicyCheckOut(
        approved=decision.approved,
        reason=decision.reason,
        risk_level=decision.risk.value,
        action=decision.action,
    )
