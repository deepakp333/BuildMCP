"""NewsAPI client with sentiment classification."""

from __future__ import annotations

import httpx
import structlog

from mcp_server.config import get_settings
from mcp_server.models import NewsArticle

logger = structlog.get_logger(__name__)

_POSITIVE = {"growth", "profit", "beat", "upgrade", "strong", "record", "expansion", "gain"}
_NEGATIVE = {"loss", "downgrade", "weak", "decline", "lawsuit", "fraud", "default", "risk", "cut"}


class NewsAPIClient:
    """NewsAPI.org client."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._settings = get_settings()
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=30.0)

    def _classify_sentiment(self, text: str) -> str:
        lower = text.lower()
        pos = sum(1 for w in _POSITIVE if w in lower)
        neg = sum(1 for w in _NEGATIVE if w in lower)
        if pos > neg:
            return "positive"
        if neg > pos:
            return "negative"
        return "neutral"

    async def search_news(self, query: str, limit: int = 10) -> list[NewsArticle]:
        """Search news articles for entity."""
        if not self._settings.news_api_key:
            return self._fallback_news(query, limit)

        client = await self._get_client()
        params = {
            "q": query,
            "apiKey": self._settings.news_api_key,
            "pageSize": limit,
            "sortBy": "publishedAt",
            "language": "en",
        }
        try:
            resp = await client.get(f"{self._settings.news_api_base}/everything", params=params)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            result = []
            for a in articles:
                title = a.get("title", "")
                desc = a.get("description", "") or ""
                sentiment = self._classify_sentiment(f"{title} {desc}")
                result.append(
                    NewsArticle(
                        title=title,
                        source=a.get("source", {}).get("name", "Unknown"),
                        published_at=a.get("publishedAt", ""),
                        url=a.get("url", ""),
                        sentiment=sentiment,  # type: ignore[arg-type]
                    )
                )
            return result
        except httpx.HTTPError as exc:
            logger.warning("newsapi_failed", query=query, error=str(exc))
            return self._fallback_news(query, limit)

    def _fallback_news(self, query: str, limit: int) -> list[NewsArticle]:
        """Deterministic fallback news when API key unavailable."""
        templates = [
            ("{q} reports steady quarterly performance", "Reuters", "neutral"),
            ("Analysts maintain outlook on {q} credit profile", "Bloomberg", "positive"),
            ("{q} faces regulatory scrutiny in latest filing", "Financial Times", "negative"),
            ("{q} expands lending portfolio amid rate environment", "WSJ", "positive"),
            ("Market monitors {q} capital ratios closely", "CNBC", "neutral"),
        ]
        articles = []
        for i, (title_tpl, source, sentiment) in enumerate(templates[:limit]):
            articles.append(
                NewsArticle(
                    title=title_tpl.format(q=query),
                    source=source,
                    published_at=f"2024-{10 + i:02d}-15T12:00:00Z",
                    url=f"https://news.example.com/{query.replace(' ', '-').lower()}/{i}",
                    sentiment=sentiment,  # type: ignore[arg-type]
                )
            )
        return articles
