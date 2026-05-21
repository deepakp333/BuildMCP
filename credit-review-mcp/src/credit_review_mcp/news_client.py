"""Trusted news collection with configurable adapters and mock fallback."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Protocol

import httpx

from credit_review_mcp.config import (
    BLOOMBERG_API_KEY,
    HTTP_TIMEOUT_SECONDS,
    NEWS_API_KEY,
    REUTERS_API_KEY,
    TRUSTED_NEWS_SOURCES,
)
from credit_review_mcp.schemas import DataProvenance, NewsArticle, NewsCollection, RetrievalMethod

logger = logging.getLogger(__name__)

# Finance-aware keyword sentiment (deterministic)
POSITIVE_KEYWORDS = (
    "beat", "upgrade", "growth", "record", "profit", "surplus", "expansion",
    "dividend increase", "strong demand", "raised guidance",
)
NEGATIVE_KEYWORDS = (
    "miss", "downgrade", "loss", "layoff", "recall", "investigation", "fraud",
    "default", "bankruptcy", "recall", "lawsuit", "cut guidance", "weak demand",
    "regulatory probe", "recall",
)


class NewsAdapter(Protocol):
    def fetch(self, ticker: str, company_name: str, limit: int = 5) -> NewsCollection: ...


def deterministic_sentiment(text: str) -> float:
    lower = text.lower()
    pos = sum(1 for k in POSITIVE_KEYWORDS if k in lower)
    neg = sum(1 for k in NEGATIVE_KEYWORDS if k in lower)
    if pos == 0 and neg == 0:
        return 0.0
    return max(-1.0, min(1.0, (pos - neg) / max(pos + neg, 1)))


def assess_news_sentiment(articles: list[NewsArticle]) -> list[NewsArticle]:
    """Re-score sentiment deterministically from title + summary."""
    updated: list[NewsArticle] = []
    for article in articles:
        score = deterministic_sentiment(f"{article.title} {article.summary}")
        updated.append(article.model_copy(update={"sentiment_score": score}))
    return updated


class MockNewsAdapter:
    """Demo news with realistic trusted-source metadata — clearly labeled mock."""

    def fetch(self, ticker: str, company_name: str, limit: int = 5) -> NewsCollection:
        now = datetime.utcnow()
        templates = [
            (
                f"{company_name} posts quarterly results in line with consensus",
                "Reuters",
                "Earnings coverage with margin commentary; no material surprise flagged in headline.",
            ),
            (
                f"Analysts review {company_name} capital allocation and balance sheet",
                "Wall Street Journal",
                "Credit-focused column discusses leverage trajectory and liquidity buffers.",
            ),
            (
                f"{company_name} files routine SEC disclosure",
                "SEC Filings",
                "Periodic filing update; analysts should verify footnotes and covenants.",
            ),
            (
                f"Sector outlook note mentions {ticker} demand trends",
                "Bloomberg",
                "Industry wire summary — macro and input-cost commentary.",
            ),
            (
                f"{company_name} investor relations update",
                "Company IR",
                "Management highlights operational priorities; qualitative only.",
            ),
        ]
        articles: list[NewsArticle] = []
        for i, (title, source, summary) in enumerate(templates[:limit]):
            published = now - timedelta(days=i + 1)
            text = f"{title} {summary}"
            articles.append(
                NewsArticle(
                    title=title,
                    source=source,
                    published_at=published,
                    url=f"https://demo.credit-review.local/news/{ticker.lower()}/{i}",
                    summary=summary,
                    relevance_score=round(0.95 - i * 0.08, 2),
                    sentiment_score=deterministic_sentiment(text),
                    is_mock=True,
                    provenance=DataProvenance(
                        source=source,
                        retrieval_method=RetrievalMethod.MOCK_DEMO,
                        notes="MOCK/DEMO news — not retrieved from live paywalled APIs",
                    ),
                )
            )
        return NewsCollection(
            ticker=ticker,
            articles=articles,
            retrieval_mode="mock_demo",
        )


class YahooNewsAdapter:
    """Pull headlines from yfinance when available."""

    def fetch(self, ticker: str, company_name: str, limit: int = 5) -> NewsCollection:
        from credit_review_mcp.yahoo_client import _get_ticker

        articles: list[NewsArticle] = []
        try:
            t = _get_ticker(ticker)
            raw = t.news or []
            for item in raw[:limit]:
                title = item.get("title", "Untitled")
                link = item.get("link", f"https://finance.yahoo.com/quote/{ticker}")
                publisher = item.get("publisher", "Yahoo Finance")
                ts = item.get("providerPublishTime")
                published = datetime.utcfromtimestamp(ts) if ts else datetime.utcnow()
                summary = item.get("summary", title)[:500]
                articles.append(
                    NewsArticle(
                        title=title,
                        source=publisher if publisher in TRUSTED_NEWS_SOURCES else "Yahoo Finance",
                        published_at=published,
                        url=link,
                        summary=summary or title,
                        relevance_score=0.85,
                        sentiment_score=deterministic_sentiment(f"{title} {summary}"),
                        is_mock=False,
                        provenance=DataProvenance(
                            source="Yahoo Finance News",
                            retrieval_method=RetrievalMethod.YAHOO_FINANCE,
                            url=link,
                        ),
                    )
                )
        except Exception as exc:
            logger.warning("Yahoo news failed for %s: %s", ticker, exc)

        if not articles:
            return MockNewsAdapter().fetch(ticker, company_name, limit)

        return NewsCollection(ticker=ticker, articles=articles[:limit], retrieval_mode="yahoo_finance")


class NewsApiAdapter:
    """Placeholder for NewsAPI.org when key present — no paywall scraping."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def fetch(self, ticker: str, company_name: str, limit: int = 5) -> NewsCollection:
        if not self.api_key:
            return MockNewsAdapter().fetch(ticker, company_name, limit)
        query = f"{company_name} OR {ticker}"
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "pageSize": limit,
            "sortBy": "publishedAt",
            "language": "en",
        }
        headers = {"X-Api-Key": self.api_key}
        articles: list[NewsArticle] = []
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
                resp = client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            for item in data.get("articles", [])[:limit]:
                source_name = (item.get("source") or {}).get("name", "NewsAPI")
                title = item.get("title", "")
                summary = item.get("description", title) or title
                published = item.get("publishedAt")
                pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else datetime.utcnow()
                articles.append(
                    NewsArticle(
                        title=title,
                        source=source_name,
                        published_at=pub_dt.replace(tzinfo=None) if pub_dt.tzinfo else pub_dt,
                        url=item.get("url", ""),
                        summary=summary[:500],
                        relevance_score=0.8,
                        sentiment_score=deterministic_sentiment(f"{title} {summary}"),
                        is_mock=False,
                        provenance=DataProvenance(
                            source=source_name,
                            retrieval_method=RetrievalMethod.YAHOO_FINANCE,
                            url=item.get("url"),
                            notes="NewsAPI adapter",
                        ),
                    )
                )
        except Exception as exc:
            logger.warning("NewsAPI fetch failed: %s", exc)
            return MockNewsAdapter().fetch(ticker, company_name, limit)

        return NewsCollection(ticker=ticker, articles=articles, retrieval_mode="newsapi")


def get_news_adapter() -> NewsAdapter:
    if NEWS_API_KEY:
        return NewsApiAdapter(NEWS_API_KEY)
    if REUTERS_API_KEY or BLOOMBERG_API_KEY:
        logger.info("Reuters/Bloomberg keys present but direct adapters not configured — using Yahoo/mock")
    return YahooNewsAdapter()


def collect_trusted_news(ticker: str, company_name: str, limit: int = 5) -> NewsCollection:
    adapter = get_news_adapter()
    collection = adapter.fetch(ticker, company_name, limit)
    collection.articles = assess_news_sentiment(collection.articles)
    return collection
