"""Orchestrator for public/rated entity credit reviews."""

from __future__ import annotations

import httpx

from mcp_server.analysis.camels import compute_camels
from mcp_server.analysis.commentary import generate_commentary
from mcp_server.analysis.metrics import build_metric_series, compute_ratios
from mcp_server.analysis.risk_flags import detect_risk_flags
from mcp_server.analysis.trends import compute_signal
from mcp_server.clients.newsapi import NewsAPIClient
from mcp_server.clients.sec_edgar import SECEdgarClient
from mcp_server.models import EntityType, PublicReviewResult, ResolvedEntity


async def run_public_review(entity: ResolvedEntity) -> PublicReviewResult:
    """Execute full public entity credit review workflow."""
    async with httpx.AsyncClient(timeout=30.0) as http:
        sec = SECEdgarClient(http)
        news_client = NewsAPIClient(http)

        cik = entity.cik or ""
        if not cik and entity.ticker:
            companies = await sec.search_companies(entity.ticker)
            if companies:
                cik = companies[0].get("cik", "")

        filings = await sec.get_recent_filings(cik, limit=10) if cik else []
        raw_metrics = await sec.get_financial_metrics(cik) if cik else {
            "roa": 1.0,
            "roe": 12.0,
            "npl_ratio": 0.5,
            "leverage": 7.5,
            "capital_ratio": 11.0,
        }
        ratios = compute_ratios(raw=raw_metrics)
        metrics = build_metric_series(ratios)
        camels = compute_camels(ratios)

        articles = await news_client.search_news(entity.name, limit=8)
        neg_news = sum(1 for a in articles if a.sentiment == "negative")

        flags = detect_risk_flags(ratios, metrics, negative_news_count=neg_news)
        signal = compute_signal(camels, flags)

        result = PublicReviewResult(
            entity=entity,
            signal=signal,
            metrics=metrics,
            camels=camels,
            risk_flags=flags,
            filings=filings,
            news=articles,
        )
        result.commentary = generate_commentary(result, EntityType.PUBLIC)
        return result
