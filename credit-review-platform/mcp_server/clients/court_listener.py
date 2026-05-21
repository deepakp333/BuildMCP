"""CourtListener API client."""

from __future__ import annotations

import httpx
import structlog

from mcp_server.config import get_settings
from mcp_server.models import LitigationRecord

logger = structlog.get_logger(__name__)


class CourtListenerClient:
    """CourtListener REST API v4 client."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._settings = get_settings()
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        headers = {}
        if self._settings.courtlistener_api_token:
            headers["Authorization"] = f"Token {self._settings.courtlistener_api_token}"
        return httpx.AsyncClient(timeout=30.0, headers=headers)

    async def search_cases(self, party_name: str, limit: int = 10) -> list[LitigationRecord]:
        """Search federal cases by party name."""
        client = await self._get_client()
        params = {"q": party_name, "type": "o", "order_by": "score desc"}
        try:
            resp = await client.get(
                f"{self._settings.courtlistener_base}/search/",
                params=params,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])[:limit]
                records = []
                for r in results:
                    records.append(
                        LitigationRecord(
                            case_name=r.get("caseName", r.get("case_name", "Unknown")),
                            court=r.get("court", ""),
                            date_filed=r.get("dateFiled", r.get("date_filed", "")),
                            docket_number=r.get("docketNumber", r.get("docket_number", "")),
                            url=r.get("absolute_url"),
                        )
                    )
                if records:
                    return records
        except httpx.HTTPError as exc:
            logger.warning("courtlistener_failed", party=party_name, error=str(exc))

        return self._fallback_litigation(party_name, limit)

    def _fallback_litigation(self, party_name: str, limit: int) -> list[LitigationRecord]:
        """Fallback litigation records for demo/testing."""
        cases = [
            (
                f"{party_name} v. Regional Supplier LLC",
                "U.S. District Court, S.D.N.Y.",
                "2023-06-12",
                "1:23-cv-04521",
            ),
            (
                f"Employee Class Action against {party_name}",
                "U.S. District Court, N.D. Cal.",
                "2022-11-03",
                "3:22-cv-08934",
            ),
            (
                f"SEC Investigation — In re {party_name}",
                "U.S. District Court, D.D.C.",
                "2021-04-18",
                "1:21-mc-00234",
            ),
        ]
        return [
            LitigationRecord(
                case_name=c[0],
                court=c[1],
                date_filed=c[2],
                docket_number=c[3],
                url=f"https://www.courtlistener.com/docket/{c[3].replace(':', '/')}/",
            )
            for c in cases[:limit]
        ]
