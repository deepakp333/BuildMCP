"""FDIC BankFind async client."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from mcp_server.config import get_settings

logger = structlog.get_logger(__name__)


class FDICClient:
    """Async client for FDIC BankFind API."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._settings = get_settings()
        self._client = client
        self._base = self._settings.fdic_api_base

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=30.0)

    async def search_institutions(self, name: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search FDIC institutions by name."""
        client = await self._get_client()
        params = {
            "filters": f'NAME:"{name}"',
            "fields": "NAME,CERT,STALP,CITY,ASSET,ACTIVE",
            "limit": limit,
            "format": "json",
        }
        url = f"{self._base}/institutions"
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            records = data.get("data", [])
            return [r.get("data", r) if isinstance(r, dict) and "data" in r else r for r in records]
        except httpx.HTTPError as exc:
            logger.warning("fdic_search_failed", name=name, error=str(exc))
            return []

    async def get_financials(
        self, cert: int, report_type: str = "total_assets", limit: int = 8
    ) -> list[dict[str, Any]]:
        """Fetch historical financial series for a certificate."""
        client = await self._get_client()
        params = {
            "filters": f"CERT:{cert}",
            "fields": f"REPDTE,{report_type.upper()}",
            "limit": limit,
            "sort_by": "REPDTE",
            "sort_order": "DESC",
            "format": "json",
        }
        url = f"{self._base}/financials"
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            records = data.get("data", [])
            result = []
            for r in records:
                row = r.get("data", r) if isinstance(r, dict) else r
                if isinstance(row, dict):
                    result.append(row)
            return result
        except httpx.HTTPError as exc:
            logger.warning("fdic_financials_failed", cert=cert, error=str(exc))
            return []

    async def get_institution_by_cert(self, cert: int) -> dict[str, Any] | None:
        """Get single institution by certificate number."""
        client = await self._get_client()
        params = {
            "filters": f"CERT:{cert}",
            "fields": "NAME,CERT,STALP,CITY,ASSET,ROA,ROE,NETINC,DEP,EQ,OFFDOM,NCLNLS",
            "limit": 1,
            "format": "json",
        }
        url = f"{self._base}/institutions"
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            records = data.get("data", [])
            if not records:
                return None
            row = records[0]
            return row.get("data", row) if isinstance(row, dict) else row
        except httpx.HTTPError as exc:
            logger.warning("fdic_institution_failed", cert=cert, error=str(exc))
            return None

    async def get_latest_ratios(self, cert: int) -> dict[str, float]:
        """Extract key ratios from latest institution and financial data."""
        inst = await self.get_institution_by_cert(cert)
        if not inst:
            return {}

        def _safe_float(val: Any, default: float = 0.0) -> float:
            try:
                if val is None or val == "":
                    return default
                return float(val)
            except (TypeError, ValueError):
                return default

        assets = _safe_float(inst.get("ASSET"), 1.0)
        equity = _safe_float(inst.get("EQ"), 0.0)
        netinc = _safe_float(inst.get("NETINC"), 0.0)
        ncl = _safe_float(inst.get("NCLNLS"), 0.0)
        offdom = _safe_float(inst.get("OFFDOM"), 0.0)

        roa = _safe_float(inst.get("ROA"))
        roe = _safe_float(inst.get("ROE"))
        if roa == 0 and assets > 0:
            roa = (netinc / assets) * 100
        if roe == 0 and equity > 0:
            roe = (netinc / equity) * 100

        npl_ratio = (ncl / offdom * 100) if offdom > 0 else 0.0
        leverage = assets / equity if equity > 0 else 0.0
        capital_ratio = (equity / assets * 100) if assets > 0 else 0.0

        return {
            "roa": roa,
            "roe": roe,
            "npl_ratio": npl_ratio,
            "leverage": leverage,
            "capital_ratio": capital_ratio,
            "total_assets": assets,
            "net_income": netinc,
        }


from typing import Any  # noqa: E402 — used in _safe_float
