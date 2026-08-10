"""
CoinMarketCap Data Adapter
===========================
Read-only adapter for the CoinMarketCap Pro API v1.
Fetches market listings and converts them to Martin Candidate objects.

Docs: https://coinmarketcap.com/api/documentation/v1/
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from martin_core.scoring import Candidate

logger = logging.getLogger(__name__)

CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"
CMC_SANDBOX_URL = "https://sandbox-api.coinmarketcap.com/v1"


class CoinMarketCapAdapter:
    """
    Read-only CoinMarketCap adapter.

    All data is fetched via GET requests using your CMC_API_KEY.
    No writes, no transactions.
    """

    def __init__(
        self,
        api_key: str | None = None,
        sandbox: bool = False,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("CMC_API_KEY", "")
        self.base_url = CMC_SANDBOX_URL if sandbox else CMC_BASE_URL
        self.timeout = timeout

        if not self.api_key:
            logger.warning(
                "CMC_API_KEY not set. Requests will fail. "
                "Set CMC_API_KEY in your .env file."
            )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_listings(
        self,
        start: int = 1,
        limit: int = 100,
        sort: str = "market_cap",
        sort_dir: str = "desc",
        convert: str = "USD",
    ) -> list[dict[str, Any]]:
        """
        Fetch cryptocurrency listings from CMC.

        Returns a list of raw CMC coin dicts.
        """
        params = {
            "start": start,
            "limit": limit,
            "sort": sort,
            "sort_dir": sort_dir,
            "convert": convert,
        }
        data = self._get("/cryptocurrency/listings/latest", params)
        return data.get("data", [])

    def get_metadata(self, ids: list[int]) -> dict[str, Any]:
        """Fetch metadata (website, logo, description) for a list of CMC IDs."""
        params = {"id": ",".join(str(i) for i in ids)}
        data = self._get("/cryptocurrency/info", params)
        return data.get("data", {})

    def listings_to_candidates(
        self,
        listings: list[dict[str, Any]],
    ) -> list[Candidate]:
        """
        Convert raw CMC listing dicts to Martin Candidate objects.

        Feature mapping:
          market_activity  ← normalized volume_24h
          liquidity        ← normalized market_cap rank (inverted)
          volume           ← normalized volume_change_24h
          onchain_activity ← placeholder (requires blockchain data)
          developer_activity ← placeholder (requires GitHub data)
          exchange_activity ← num_market_pairs normalized
          project_health   ← percent_change_7d trend signal
          recovery_evidence ← 0 (requires additional enrichment)
          ownership_evidence ← 0 (requires wallet scan)
        """
        candidates = []
        for coin in listings:
            try:
                candidate = self._coin_to_candidate(coin)
                candidates.append(candidate)
            except (ValueError, KeyError, TypeError) as exc:
                logger.debug("Skipping coin %s: %s", coin.get("symbol"), exc)
        return candidates

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _coin_to_candidate(self, coin: dict[str, Any]) -> Candidate:
        quote = coin.get("quote", {}).get("USD", {})

        # Normalize market cap rank [0,1] — rank 1 → 1.0, rank 5000 → ~0
        rank = coin.get("cmc_rank", 5000)
        liquidity = max(0.0, 1.0 - (rank - 1) / 5000.0)

        # Volume signal: normalize log(volume_24h)
        vol_24h = max(0.0, quote.get("volume_24h", 0) or 0)
        market_activity = min(1.0, _log_norm(vol_24h, scale=1e9))

        # Volume change — signal for activity
        vol_change = abs(quote.get("volume_change_24h", 0) or 0)
        volume = min(1.0, vol_change / 100.0)

        # Exchange activity: num_market_pairs normalized
        pairs = coin.get("num_market_pairs", 0) or 0
        exchange_activity = min(1.0, pairs / 500.0)

        # Project health: 7d price trend
        pct_7d = quote.get("percent_change_7d", 0) or 0
        # Map [-100, +100] to [0, 1]
        project_health = min(1.0, max(0.0, (pct_7d + 100.0) / 200.0))

        # Risk: volatility proxy from 24h change
        pct_24h = abs(quote.get("percent_change_24h", 0) or 0)
        risk = min(1.0, pct_24h / 50.0)

        # Confidence: how complete is the data?
        confidence = 0.5 if vol_24h > 0 else 0.1

        features = {
            "market_activity":    market_activity,
            "liquidity":          liquidity,
            "volume":             volume,
            "onchain_activity":   0.0,   # enriched by blockchain adapter
            "developer_activity": 0.0,   # enriched by GitHub adapter
            "exchange_activity":  exchange_activity,
            "project_health":     project_health,
            "recovery_evidence":  0.0,   # enriched by recovery agent
            "ownership_evidence": 0.0,   # enriched by wallet scanner
        }

        return Candidate(
            asset_id=f"cmc:{coin.get('id', 0)}:{coin.get('symbol', 'UNKNOWN')}",
            features=features,
            risk=risk,
            confidence=confidence,
        )

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        headers = {
            "X-CMC_PRO_API_KEY": self.api_key,
            "Accept": "application/json",
        }
        url = self.base_url + path
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("CMC API error %s: %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.RequestError as exc:
            logger.error("CMC request failed: %s", exc)
            raise


def _log_norm(value: float, scale: float = 1e9) -> float:
    """Log-normalize a value relative to a scale factor."""
    import math
    if value <= 0:
        return 0.0
    return min(1.0, math.log1p(value) / math.log1p(scale))
