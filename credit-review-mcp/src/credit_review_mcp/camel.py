"""Adapted CAMEL framework scoring for public-company credit review."""

from __future__ import annotations

from datetime import datetime

from credit_review_mcp.schemas import (
    CamelAssessment,
    CamelComponentScore,
    CompanyFinancials,
    CreditRatioSet,
    MarketData,
    NewsCollection,
)


def _clamp_score(score: float) -> int:
    return max(1, min(5, round(score)))


def _avg_component_scores(components: list[CamelComponentScore]) -> float:
    if not components:
        return 0.0
    return sum(c.score for c in components) / len(components)


def _get_ratio(ratios: CreditRatioSet | None, name: str) -> float | None:
    if not ratios:
        return None
    for r in ratios.ratios:
        if r.name == name:
            return r.value
    return None


def run_camel_assessment(
    *,
    fin: CompanyFinancials | None,
    ratios: CreditRatioSet | None,
    market: MarketData | None,
    news: NewsCollection | None,
    company_name: str,
    ticker: str,
) -> CamelAssessment:
    components: list[CamelComponentScore] = []
    components.append(_score_capital(fin, ratios))
    components.append(_score_asset_quality(fin, ratios))
    components.append(_score_management(news, fin))
    components.append(_score_earnings(fin, ratios))
    components.append(_score_liquidity(fin, ratios, market))

    overall = _avg_component_scores(components)
    return CamelAssessment(
        ticker=ticker,
        company_name=company_name,
        as_of=datetime.utcnow(),
        components=components,
        overall_score=round(overall, 2),
        overall_rationale=(
            f"Composite CAMEL average score {overall:.2f} (1=strong, 5=weak). "
            "Scores are deterministic rules-based estimates for demo purposes."
        ),
    )


def _score_capital(fin: CompanyFinancials | None, ratios: CreditRatioSet | None) -> CamelComponentScore:
    missing: list[str] = []
    metrics: dict[str, float | str | None] = {}
    score = 3.0

    de = _get_ratio(ratios, "Debt / Equity")
    d_ebitda = _get_ratio(ratios, "Debt / EBITDA")
    metrics["debt_equity"] = de
    metrics["debt_ebitda"] = d_ebitda

    if de is None and d_ebitda is None:
        missing.append("Leverage ratios unavailable")
        score = 3.5
    else:
        if de is not None:
            if de < 0.5:
                score -= 0.8
            elif de > 2.0:
                score += 1.2
            elif de > 1.0:
                score += 0.5
        if d_ebitda is not None:
            if d_ebitda < 2:
                score -= 0.5
            elif d_ebitda > 5:
                score += 1.0
            elif d_ebitda > 3:
                score += 0.4

    retained = fin.metrics.get("retained_earnings").value if fin and fin.metrics.get("retained_earnings") else None
    metrics["retained_earnings"] = retained
    if retained is not None and retained < 0:
        score += 0.6
        metrics["retained_earnings_flag"] = "negative"

    return CamelComponentScore(
        component="Capital Adequacy",
        score=_clamp_score(score),
        rationale="Assesses leverage, debt service capacity proxies, and equity cushion.",
        supporting_metrics=metrics,
        confidence="low" if missing else "medium",
        missing_data_warnings=missing,
    )


def _score_asset_quality(fin: CompanyFinancials | None, ratios: CreditRatioSet | None) -> CamelComponentScore:
    missing: list[str] = []
    metrics: dict[str, float | str | None] = {}
    score = 3.0

    current = _get_ratio(ratios, "Current Ratio")
    metrics["current_ratio"] = current
    if current is None:
        missing.append("Current ratio unavailable")
    elif current < 1.0:
        score += 1.0
    elif current > 1.5:
        score -= 0.5

    goodwill = fin.metrics.get("goodwill").value if fin and fin.metrics.get("goodwill") else None
    total_assets = fin.metrics.get("total_assets").value if fin and fin.metrics.get("total_assets") else None
    if goodwill is not None and total_assets:
        conc = goodwill / total_assets if total_assets else None
        metrics["goodwill_to_assets"] = conc
        if conc and conc > 0.25:
            score += 0.5
            metrics["intangible_concentration"] = "elevated"

    receivables = fin.metrics.get("receivables").value if fin and fin.metrics.get("receivables") else None
    revenue = fin.metrics.get("revenue").value if fin and fin.metrics.get("revenue") else None
    if receivables and revenue:
        dso_proxy = (receivables / revenue) * 365 if revenue else None
        metrics["receivables_days_proxy"] = dso_proxy
        if dso_proxy and dso_proxy > 90:
            score += 0.4

    return CamelComponentScore(
        component="Asset Quality",
        score=_clamp_score(score),
        rationale="Working capital, receivables/inventory signals, and intangible concentration.",
        supporting_metrics=metrics,
        confidence="low" if len(missing) > 1 else "medium",
        missing_data_warnings=missing,
    )


def _score_management(
    news: NewsCollection | None,
    fin: CompanyFinancials | None,
) -> CamelComponentScore:
    metrics: dict[str, float | str | None] = {}
    missing: list[str] = []
    score = 3.0

    if news and news.articles:
        neg = sum(1 for a in news.articles if a.sentiment_score < -0.2)
        metrics["negative_news_count"] = neg
        if neg >= 2:
            score += 0.8
        elif neg == 0:
            score -= 0.3
    else:
        missing.append("No news items for governance/red-flag scan")

    if fin and fin.warnings:
        filing_issues = len([w for w in fin.warnings if "filing" in w.lower() or "late" in w.lower()])
        metrics["filing_warnings"] = filing_issues
        if filing_issues:
            score += 0.5

    return CamelComponentScore(
        component="Management Capability",
        score=_clamp_score(score),
        rationale="Governance/news red flags, filing quality signals (qualitative demo proxies).",
        supporting_metrics=metrics,
        confidence="low",
        missing_data_warnings=missing,
    )


def _score_earnings(fin: CompanyFinancials | None, ratios: CreditRatioSet | None) -> CamelComponentScore:
    missing: list[str] = []
    metrics: dict[str, float | str | None] = {}
    score = 3.0

    rev_g = _get_ratio(ratios, "Revenue Growth YoY")
    ebitda_m = _get_ratio(ratios, "EBITDA Margin")
    fcf_debt = _get_ratio(ratios, "Free Cash Flow / Debt")
    metrics["revenue_growth_yoy"] = rev_g
    metrics["ebitda_margin"] = ebitda_m
    metrics["fcf_to_debt"] = fcf_debt

    if rev_g is None:
        missing.append("Revenue growth unavailable")
    elif rev_g < 0:
        score += 0.7
    elif rev_g > 0.05:
        score -= 0.5

    if ebitda_m is None:
        missing.append("EBITDA margin unavailable")
    elif ebitda_m < 0.1:
        score += 0.6
    elif ebitda_m > 0.25:
        score -= 0.4

    ni = fin.metrics.get("net_income").value if fin and fin.metrics.get("net_income") else None
    metrics["net_income"] = ni
    if ni is not None and ni < 0:
        score += 0.5

    return CamelComponentScore(
        component="Earnings",
        score=_clamp_score(score),
        rationale="Revenue/margin trends, profitability, and cash generation proxies.",
        supporting_metrics=metrics,
        confidence="medium" if not missing else "low",
        missing_data_warnings=missing,
    )


def _score_liquidity(
    fin: CompanyFinancials | None,
    ratios: CreditRatioSet | None,
    market: MarketData | None,
) -> CamelComponentScore:
    missing: list[str] = []
    metrics: dict[str, float | str | None] = {}
    score = 3.0

    current = _get_ratio(ratios, "Current Ratio")
    cash_debt = _get_ratio(ratios, "Cash / Debt")
    fcf_debt = _get_ratio(ratios, "Free Cash Flow / Debt")
    metrics["current_ratio"] = current
    metrics["cash_to_debt"] = cash_debt
    metrics["fcf_to_debt"] = fcf_debt

    if current is None:
        missing.append("Current ratio unavailable")
    elif current < 1.0:
        score += 1.0
    elif current > 2.0:
        score -= 0.4

    cash = fin.metrics.get("cash_and_equivalents").value if fin and fin.metrics.get("cash_and_equivalents") else None
    metrics["cash"] = cash
    if cash_debt is not None and cash_debt > 0.3:
        score -= 0.3
    elif cash_debt is not None and cash_debt < 0.05:
        score += 0.5

    if market and market.price:
        metrics["share_price"] = market.price

    return CamelComponentScore(
        component="Liquidity",
        score=_clamp_score(score),
        rationale="Short-term liquidity, cash buffers, and FCF relative to debt.",
        supporting_metrics=metrics,
        confidence="medium" if len(missing) < 2 else "low",
        missing_data_warnings=missing,
    )
