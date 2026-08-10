"""
Scanner Agent
=============
Autonomous agent that periodically scans CoinMarketCap for dormant,
dead, and recoverable crypto assets and scores them using Martin's Algorithm.

The agent is READ-ONLY. It never initiates transactions.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from data.coinmarketcap import CoinMarketCapAdapter
from martin_core.classifier import AssetStatus, ClassificationResult, batch_classify
from martin_core.policy import ActionRequest, PolicyEngine, RiskLevel
from martin_core.scoring import Candidate

logger = logging.getLogger(__name__)

policy = PolicyEngine()


@dataclass
class ScanResult:
    """Result of a single scan pass."""
    scan_id: str
    timestamp: float
    total_scanned: int
    opportunities: list[ClassificationResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def recoverable(self) -> list[ClassificationResult]:
        return [r for r in self.opportunities if r.status == AssetStatus.RECOVERABLE]

    @property
    def dormant(self) -> list[ClassificationResult]:
        return [r for r in self.opportunities if r.status in (
            AssetStatus.DORMANT, AssetStatus.DEAD, AssetStatus.MIGRATED
        )]


class ScannerAgent:
    """
    Autonomous CoinMarketCap scanner agent.

    Runs periodic scans and surfaces recovery opportunities.
    All data fetches go through PolicyEngine (READ_ONLY — no approval needed).
    """

    def __init__(
        self,
        cmc_adapter: CoinMarketCapAdapter | None = None,
        scan_interval: int = 3600,
        pages: int = 5,
        page_size: int = 100,
    ) -> None:
        self.cmc = cmc_adapter or CoinMarketCapAdapter()
        self.scan_interval = scan_interval  # seconds between scans
        self.pages = pages
        self.page_size = page_size
        self._results: list[ScanResult] = []
        self._running = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def scan_once(self, top_k_opportunities: int = 50) -> ScanResult:
        """
        Run a single scan pass synchronously.
        Returns a ScanResult with classified opportunities.
        """
        # Policy check — READ_ONLY, no approval needed
        decision = policy.authorize(ActionRequest(
            action="scan_coinmarketcap",
            asset_id=None,
            value=0.0,
            risk=RiskLevel.READ_ONLY,
        ))
        if not decision.approved:
            raise PermissionError(f"Policy denied scan: {decision.reason}")

        scan_id = f"scan_{int(time.time())}"
        timestamp = time.time()
        candidates: list[Candidate] = []
        errors: list[str] = []

        logger.info("Starting scan %s (%d pages x %d)", scan_id, self.pages, self.page_size)

        for page in range(self.pages):
            start = page * self.page_size + 1
            try:
                listings = self.cmc.get_listings(start=start, limit=self.page_size)
                page_candidates = self.cmc.listings_to_candidates(listings)
                candidates.extend(page_candidates)
                logger.debug("Page %d: %d candidates", page + 1, len(page_candidates))
            except (ValueError, KeyError, TypeError) as exc:
                msg = f"Page {page + 1} failed: {exc}"
                logger.warning(msg)
                errors.append(msg)

        # Classify all candidates
        all_results = batch_classify(candidates)

        # Filter to interesting statuses only
        interesting_statuses = {
            AssetStatus.RECOVERABLE,
            AssetStatus.DORMANT,
            AssetStatus.DEAD,
            AssetStatus.MIGRATED,
            AssetStatus.REBRANDED,
        }
        opportunities = [
            r for r in all_results
            if r.status in interesting_statuses
        ][:top_k_opportunities]

        result = ScanResult(
            scan_id=scan_id,
            timestamp=timestamp,
            total_scanned=len(candidates),
            opportunities=opportunities,
            errors=errors,
        )
        self._results.append(result)
        logger.info(
            "Scan %s complete: %d scanned, %d opportunities found",
            scan_id, len(candidates), len(opportunities),
        )
        return result

    def get_latest_result(self) -> ScanResult | None:
        """Return the most recent scan result."""
        return self._results[-1] if self._results else None

    def get_all_results(self) -> list[ScanResult]:
        return list(self._results)

    async def run_continuous(self) -> None:
        """Run continuous scanning in an async loop."""
        self._running = True
        logger.info("Scanner agent started. Interval: %ds", self.scan_interval)
        while self._running:
            try:
                self.scan_once()
            except (ValueError, KeyError, TypeError, PermissionError) as exc:
                logger.error("Scan failed: %s", exc)
            await asyncio.sleep(self.scan_interval)

    def stop(self) -> None:
        self._running = False
        logger.info("Scanner agent stopped.")
