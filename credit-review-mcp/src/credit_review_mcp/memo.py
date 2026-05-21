"""Credit memo generation — deterministic template with optional LLM narrative."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from credit_review_mcp.config import DISCLAIMER
from credit_review_mcp.llm_client import llm_available, synthesize_memo_narrative
from credit_review_mcp.schemas import (
    CamelAssessment,
    CompanyFinancials,
    CompanyRecord,
    CreditMemo,
    CreditRatioSet,
    MarketData,
    MemoSection,
    NewsCollection,
)


def _format_ratio_line(ratio_name: str, ratios: CreditRatioSet | None) -> str:
    if not ratios:
        return f"- {ratio_name}: N/A"
    for r in ratios.ratios:
        if r.name == ratio_name:
            if r.value is None:
                return f"- {r.name}: N/A ({', '.join(r.missing_inputs) or 'missing inputs'})"
            val = r.value
            if r.unit == "percent":
                val = f"{val:.1%}" if abs(val) < 10 else f"{val:.2f}"
            else:
                val = f"{val:.2f}"
            return f"- {r.name}: {val} — {r.formula}"
    return f"- {ratio_name}: N/A"


def _camel_section(camel: CamelAssessment | None) -> str:
    if not camel:
        return "CAMEL assessment unavailable."
    lines = []
    for c in camel.components:
        lines.append(
            f"**{c.component}** — Score {c.score}/5 ({'stronger' if c.score <= 2 else 'weaker' if c.score >= 4 else 'moderate'})\n"
            f"  Rationale: {c.rationale}\n"
            f"  Confidence: {c.confidence}"
        )
        if c.missing_data_warnings:
            lines.append(f"  Warnings: {'; '.join(c.missing_data_warnings)}")
    lines.append(f"\nOverall CAMEL average: {camel.overall_score} — {camel.overall_rationale}")
    return "\n".join(lines)


def _news_section(news: NewsCollection | None) -> str:
    if not news or not news.articles:
        return "No news items collected."
    mode = "MOCK/DEMO" if news.retrieval_mode == "mock_demo" or any(a.is_mock for a in news.articles) else news.retrieval_mode
    lines = [f"News retrieval mode: {mode}"]
    for a in news.articles[:5]:
        mock_flag = " [MOCK]" if a.is_mock else ""
        lines.append(
            f"- ({a.published_at.date()}) {a.source}{mock_flag}: {a.title}\n"
            f"  Sentiment: {a.sentiment_score:+.2f} | Relevance: {a.relevance_score:.2f}\n"
            f"  {a.summary[:200]}"
        )
    avg_sent = sum(a.sentiment_score for a in news.articles) / len(news.articles)
    lines.append(f"\nAverage headline sentiment (deterministic): {avg_sent:+.2f}")
    return "\n".join(lines)


def build_compact_payload(
    company: CompanyRecord,
    fin: CompanyFinancials | None,
    market: MarketData | None,
    ratios: CreditRatioSet | None,
    news: NewsCollection | None,
    camel: CamelAssessment | None,
) -> dict[str, Any]:
    """Compact JSON for LLM — never full SEC filings."""
    metrics_summary = {}
    if fin:
        for k, v in fin.metrics.items():
            metrics_summary[k] = {"value": v.value, "period": v.period}
    ratio_summary = []
    if ratios:
        for r in ratios.ratios:
            ratio_summary.append(
                {"name": r.name, "value": r.value, "missing": r.missing_inputs}
            )
    news_summary = []
    if news:
        for a in news.articles[:5]:
            news_summary.append(
                {
                    "title": a.title,
                    "source": a.source,
                    "sentiment": a.sentiment_score,
                    "is_mock": a.is_mock,
                    "summary": a.summary[:300],
                }
            )
    camel_summary = []
    if camel:
        for c in camel.components:
            camel_summary.append(
                {
                    "component": c.component,
                    "score": c.score,
                    "rationale": c.rationale,
                    "metrics": c.supporting_metrics,
                }
            )
    return {
        "company": company.model_dump(),
        "metrics_summary": metrics_summary,
        "market": market.model_dump() if market else None,
        "ratios": ratio_summary,
        "altman_warnings": ratios.altman_warnings if ratios else [],
        "news": news_summary,
        "camel": camel_summary,
        "disclaimer": DISCLAIMER,
    }


def generate_deterministic_memo(
    company: CompanyRecord,
    fin: CompanyFinancials | None,
    market: MarketData | None,
    ratios: CreditRatioSet | None,
    news: NewsCollection | None,
    camel: CamelAssessment | None,
) -> CreditMemo:
    as_of = datetime.utcnow().strftime("%Y-%m-%d")
    ticker = company.ticker or "N/A"
    name = company.company_name

    sources: list[str] = []
    if fin and fin.metrics:
        sources.append("SEC EDGAR companyfacts / Yahoo Finance fallbacks")
    if market:
        sources.append(market.provenance.source)
    if news:
        sources.append(f"News ({news.retrieval_mode})")
    sources.append("Deterministic ratio engine")
    sources.append("CAMEL rules-based scorer")

    ratio_names = [
        "Debt / EBITDA",
        "Debt / Equity",
        "Interest Coverage",
        "EBITDA Margin",
        "Current Ratio",
        "Revenue Growth YoY",
        "Free Cash Flow / Debt",
    ]
    ratio_text = "\n".join(_format_ratio_line(n, ratios) for n in ratio_names)
    if ratios and ratios.altman_warnings:
        ratio_text += "\n\nAltman-style indicators:\n" + "\n".join(f"- {w}" for w in ratios.altman_warnings)

    fin_lines = []
    if fin:
        for key in ("revenue", "ebitda", "net_income", "total_debt", "cash_and_equivalents"):
            pt = fin.metrics.get(key)
            if pt and pt.value is not None:
                fin_lines.append(f"- {key}: ${pt.value:,.0f}")
    if not fin_lines:
        fin_lines.append("- Limited financial metrics available — see data gaps.")

    market_line = ""
    if market:
        market_line = (
            f"Price: {market.price or 'N/A'} | Market Cap: "
            f"{f'${market.market_cap:,.0f}' if market.market_cap else 'N/A'} | Beta: {market.beta or 'N/A'}"
        )

    sections = [
        MemoSection(
            title="Executive Summary",
            content=(
                f"Draft credit review for {name} ({ticker}) as of {as_of}. "
                f"This is a demo workflow output for analyst review only. "
                f"CAMEL composite score (1=strong, 5=weak): "
                f"{camel.overall_score if camel else 'N/A'}. "
                f"{DISCLAIMER}"
            ),
        ),
        MemoSection(
            title="Business Overview",
            content=(
                f"{name} operates in the {company.sector or 'unspecified'} sector. "
                f"Public equity ticker: {ticker}. "
                "Analyst should validate business model, geographic mix, and peer group."
            ),
        ),
        MemoSection(
            title="Recent Developments and News Sentiment",
            content=_news_section(news),
        ),
        MemoSection(
            title="Financial Performance",
            content="\n".join(fin_lines) + ("\n" + market_line if market_line else ""),
        ),
        MemoSection(title="Key Credit Ratios", content=ratio_text),
        MemoSection(title="CAMEL Assessment", content=_camel_section(camel)),
        MemoSection(
            title="Key Risks",
            content=(
                "- Leverage and refinancing risk if Debt/EBITDA elevated\n"
                "- Earnings volatility and margin compression\n"
                "- Liquidity stress if current ratio below 1.0\n"
                "- Negative news sentiment clusters\n"
                "- Data gaps in SEC tags or market feeds"
            ),
        ),
        MemoSection(
            title="Mitigants",
            content=(
                "- Cash balances and FCF generation\n"
                "- Diversified revenue base (subject to verification)\n"
                "- Public market access and equity cushion\n"
                "- Covenant headroom (not modeled in demo)"
            ),
        ),
        MemoSection(
            title="Monitoring Triggers",
            content=(
                "- Debt/EBITDA > 4.0x or sustained negative FCF\n"
                "- Current ratio < 1.0 for two consecutive periods\n"
                "- Material negative regulatory or litigation headlines\n"
                "- Missed filing deadlines or going-concern language"
            ),
        ),
        MemoSection(
            title="Data Gaps and Analyst Review Required",
            content=(
                "All figures require analyst verification against primary filings. "
                + ("; ".join(fin.warnings) if fin and fin.warnings else "No SEC warnings recorded.")
                + "\n\n" + DISCLAIMER
            ),
        ),
        MemoSection(
            title="Appendix: Sources and Calculation Notes",
            content="Sources:\n- " + "\n- ".join(sources) + "\n\nRatios computed deterministically per documented formulas.",
        ),
    ]

    return CreditMemo(
        ticker=ticker,
        company_name=name,
        as_of_date=as_of,
        disclaimer=DISCLAIMER,
        sections=sections,
        sources=sources,
        llm_used=False,
    )


def generate_credit_memo(
    company: CompanyRecord,
    fin: CompanyFinancials | None,
    market: MarketData | None,
    ratios: CreditRatioSet | None,
    news: NewsCollection | None,
    camel: CamelAssessment | None,
) -> CreditMemo:
    memo = generate_deterministic_memo(company, fin, market, ratios, news, camel)

    if llm_available():
        payload = build_compact_payload(company, fin, market, ratios, news, camel)
        narrative, usage = synthesize_memo_narrative(payload)
        if narrative.strip():
            memo.sections.insert(
                1,
                MemoSection(
                    title="LLM Narrative Synthesis (Analyst Review Required)",
                    content=narrative,
                ),
            )
            memo.llm_used = True
            memo.token_usage = usage

    return memo


def memo_to_markdown(memo: CreditMemo) -> str:
    lines = [
        f"# Draft Credit Memo: {memo.company_name} ({memo.ticker})",
        f"**As of:** {memo.as_of_date} | **Generated:** {memo.generated_at.isoformat()}",
        f"**{memo.disclaimer}**",
        "",
    ]
    for section in memo.sections:
        lines.append(f"## {section.title}")
        lines.append(section.content)
        lines.append("")
    return "\n".join(lines)
