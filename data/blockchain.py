"""
Blockchain Read-Only Adapter
=============================
Fetches on-chain data for crypto assets using public block explorer APIs.

Supported chains:
  - Ethereum  (Etherscan)
  - BNB Chain (BscScan)
  - (extensible to Polygon, Avalanche, etc.)

All operations are READ-ONLY. No transaction signing or broadcasting.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContractInfo:
    address: str
    chain: str
    is_verified: bool
    tx_count_estimate: int    # recent tx count (proxy for activity)
    has_liquidity: bool
    is_proxy: bool


CHAIN_CONFIG: dict[str, dict[str, str]] = {
    "ethereum": {
        "base_url": "https://api.etherscan.io/api",
        "env_key":  "ETHERSCAN_API_KEY",
    },
    "bsc": {
        "base_url": "https://api.bscscan.com/api",
        "env_key":  "BSCSCAN_API_KEY",
    },
}


class BlockchainAdapter:
    """
    Read-only blockchain data adapter.
    Queries public block explorer APIs to enrich Martin candidate features.
    """

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout
        self._api_keys: dict[str, str] = {
            chain: os.getenv(cfg["env_key"], "")
            for chain, cfg in CHAIN_CONFIG.items()
        }

    def get_contract_info(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> ContractInfo | None:
        """
        Fetch basic contract information for an ERC-20 token address.

        Returns None if the contract cannot be verified or the chain is unsupported.
        """
        if chain not in CHAIN_CONFIG:
            logger.warning("Unsupported chain: %s", chain)
            return None

        cfg = CHAIN_CONFIG[chain]
        api_key = self._api_keys.get(chain, "")
        base_url = cfg["base_url"]

        # Check if contract is verified
        is_verified = self._is_verified(base_url, address, api_key)

        # Estimate tx count (last 10k txs)
        tx_count = self._estimate_tx_activity(base_url, address, api_key)

        return ContractInfo(
            address=address,
            chain=chain,
            is_verified=is_verified,
            tx_count_estimate=tx_count,
            has_liquidity=tx_count > 10,
            is_proxy=False,  # simplified — full proxy detection requires ABI analysis
        )

    def enrich_onchain_score(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> float:
        """
        Return an on-chain activity score in [0, 1] for a token address.
        Used to populate the 'onchain_activity' feature in Martin Candidates.
        """
        info = self.get_contract_info(address, chain)
        if info is None:
            return 0.0

        score = 0.0
        if info.is_verified:
            score += 0.30
        if info.has_liquidity:
            score += 0.40
        # tx activity score: 0 txs → 0.0, 1000+ txs → 0.30
        score += min(0.30, info.tx_count_estimate / 1000.0 * 0.30)
        return min(1.0, score)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_verified(self, base_url: str, address: str, api_key: str) -> bool:
        params = {
            "module":  "contract",
            "action":  "getabi",
            "address": address,
            "apikey":  api_key,
        }
        try:
            resp = self._get(base_url, params)
            return resp.get("status") == "1"
        except Exception:
            return False

    def _estimate_tx_activity(
        self, base_url: str, address: str, api_key: str
    ) -> int:
        params = {
            "module":     "account",
            "action":     "tokentx",
            "contractaddress": address,
            "startblock": 0,
            "endblock":   99999999,
            "page":       1,
            "offset":     100,
            "sort":       "desc",
            "apikey":     api_key,
        }
        try:
            resp = self._get(base_url, params)
            txs = resp.get("result", [])
            if isinstance(txs, list):
                return len(txs)
            return 0
        except Exception:
            return 0

    def _get(self, url: str, params: dict) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
