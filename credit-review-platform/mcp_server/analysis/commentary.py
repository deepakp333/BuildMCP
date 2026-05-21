"""Deterministic narrative commentary generator."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from mcp_server.models import (
    EntityType,
    PrivateReviewResult,
    PublicReviewResult,
    Signal,
)


def _signal_phrase(signal: Signal) -> str:
    return {
        Signal.STRONG: "strong credit profile with limited near-term concerns",
        Signal.ADEQUATE: "adequate credit profile within policy parameters",
        Signal.WATCH: "developing credit profile requiring enhanced monitoring",
        Signal.WEAK: "weakened credit profile with material risk factors",
    }[signal]


def generate_commentary(
    result: PublicReviewResult | PrivateReviewResult,
    entity_type: EntityType,
) -> str:
    """Generate full deterministic commentary for a review result."""
    entity = result.entity
    signal = result.signal
    flags = result.risk_flags
    camels = result.camels

    sections = []

    sections.append(
        f"CREDIT REVIEW — {entity.name.upper()}\n"
        f"Entity Type: {entity_type.value.title()} | Signal: {signal.value.upper()}\n"
        f"{'=' * 60}\n"
    )

    sections.append(
        f"EXECUTIVE SUMMARY\n"
        f"This review assesses {entity.name} as presenting a {_signal_phrase(signal)}. "
        f"Match confidence: {entity.match_score:.0f}%.\n"
    )

    if camels:
        sections.append(
            f"\nCAMELS ANALYSIS\n"
            f"  Capital:        {camels.capital:.1f}/5.0\n"
            f"  Asset Quality:  {camels.asset_quality:.1f}/5.0\n"
            f"  Management:     {camels.management:.1f}/5.0\n"
            f"  Earnings:       {camels.earnings:.1f}/5.0\n"
            f"  Liquidity:      {camels.liquidity:.1f}/5.0\n"
            f"  Sensitivity:    {camels.sensitivity:.1f}/5.0\n"
            f"  Composite:      {camels.composite:.1f}/5.0\n"
        )

    if result.metrics:
        sections.append("\nKEY METRICS\n")
        for m in result.metrics[:5]:
            trend = f" ({m.trend_direction})" if m.trend_direction else ""
            latest = m.points[-1].value if m.points else 0
            sections.append(f"  • {m.label}: {latest:.2f}{m.unit}{trend}\n")

    if flags:
        sections.append(f"\nRISK FLAGS ({len(flags)} triggered)\n")
        for f in flags:
            sections.append(f"  [{f.severity.upper()}] {f.message}\n")
    else:
        sections.append("\nRISK FLAGS\n  No material threshold breaches detected.\n")

    if isinstance(result, PublicReviewResult):
        sections.append(f"\nSEC FILINGS\n  {len(result.filings)} recent filings reviewed.\n")
        neg_news = sum(1 for n in result.news if n.sentiment == "negative")
        pos_news = sum(1 for n in result.news if n.sentiment == "positive")
        sections.append(
            f"\nNEWS SENTIMENT\n"
            f"  {len(result.news)} articles analyzed: "
            f"{pos_news} positive, {neg_news} negative.\n"
        )
    else:
        if result.trade_signals:
            ts = result.trade_signals
            sections.append(
                f"\nTRADE SIGNALS\n"
                f"  Payment Index: {ts.payment_index:.0f} | "
                f"Delinquency: {ts.delinquency_rate:.1f}% | "
                f"Rating: {ts.trade_credit_rating}\n"
            )
        sections.append(f"\nLITIGATION\n  {len(result.litigation)} matters identified.\n")

    sections.append(
        f"\nRECOMMENDATION\n"
        f"Based on quantitative analysis, maintain {signal.value} classification. "
        f"{'Immediate escalation recommended.' if signal == Signal.WEAK else 'Continue standard monitoring cycle.'}\n"
    )

    return "".join(sections)


async def stream_commentary_chunks(
    text: str,
    chunk_size: int = 80,
    delay: float = 0.02,
) -> AsyncIterator[str]:
    """Stream commentary text in chunks for WebSocket delivery."""
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]
        await asyncio.sleep(delay)
    yield ""
