"""Deterministic credit ratio calculations."""

from __future__ import annotations

from datetime import datetime

from credit_review_mcp.schemas import (
    CompanyFinancials,
    CreditRatio,
    CreditRatioSet,
    DataProvenance,
    RetrievalMethod,
)
from credit_review_mcp.utils import safe_divide


def _metric(fin: CompanyFinancials, key: str) -> float | None:
    point = fin.metrics.get(key)
    return point.value if point else None


def _ratio(
    name: str,
    formula: str,
    value: float | None,
    inputs: dict[str, float | None],
    missing: list[str],
    unit: str = "ratio",
    interpretation: str | None = None,
) -> CreditRatio:
    return CreditRatio(
        name=name,
        formula=formula,
        value=value,
        unit=unit,
        interpretation=interpretation,
        inputs_used=inputs,
        missing_inputs=missing,
        provenance=DataProvenance(
            source="credit_review_mcp.ratios",
            retrieval_method=RetrievalMethod.DETERMINISTIC,
        ),
    )


def calculate_credit_ratios(fin: CompanyFinancials) -> CreditRatioSet:
    """Compute standard credit ratios from normalized financial metrics."""
    debt = _metric(fin, "total_debt") or _metric(fin, "long_term_debt")
    ebitda = _metric(fin, "ebitda")
    equity = _metric(fin, "stockholders_equity") or _metric(fin, "total_equity")
    interest_expense = _metric(fin, "interest_expense")
    revenue = _metric(fin, "revenue")
    operating_income = _metric(fin, "operating_income")
    current_assets = _metric(fin, "current_assets")
    current_liabilities = _metric(fin, "current_liabilities")
    inventory = _metric(fin, "inventory")
    cash = _metric(fin, "cash_and_equivalents")
    fcf = _metric(fin, "free_cash_flow")
    total_liabilities = _metric(fin, "total_liabilities")
    total_assets = _metric(fin, "total_assets")
    revenue_prior = _metric(fin, "revenue_prior_year")
    ebitda_prior = _metric(fin, "ebitda_prior_year")

    ratios: list[CreditRatio] = []

    def add(name: str, formula: str, val: float | None, inputs: dict, missing: list, **kw):
        ratios.append(_ratio(name, formula, val, inputs, missing, **kw))

    add(
        "Debt / EBITDA",
        "Total Debt / EBITDA",
        safe_divide(debt, ebitda),
        {"debt": debt, "ebitda": ebitda},
        [k for k, v in {"debt": debt, "ebitda": ebitda}.items() if v is None],
    )
    add(
        "Debt / Equity",
        "Total Debt / Stockholders' Equity",
        safe_divide(debt, equity),
        {"debt": debt, "equity": equity},
        [k for k, v in {"debt": debt, "equity": equity}.items() if v is None],
    )
    add(
        "Interest Coverage",
        "EBITDA / Interest Expense",
        safe_divide(ebitda, abs(interest_expense)) if interest_expense else None,
        {"ebitda": ebitda, "interest_expense": interest_expense},
        [k for k, v in {"ebitda": ebitda, "interest_expense": interest_expense}.items() if v is None],
    )
    add(
        "EBITDA Margin",
        "EBITDA / Revenue",
        safe_divide(ebitda, revenue),
        {"ebitda": ebitda, "revenue": revenue},
        [k for k, v in {"ebitda": ebitda, "revenue": revenue}.items() if v is None],
        unit="percent",
        interpretation="Higher margin indicates stronger operating profitability.",
    )
    add(
        "Operating Margin",
        "Operating Income / Revenue",
        safe_divide(operating_income, revenue),
        {"operating_income": operating_income, "revenue": revenue},
        [k for k, v in {"operating_income": operating_income, "revenue": revenue}.items() if v is None],
        unit="percent",
    )
    add(
        "Current Ratio",
        "Current Assets / Current Liabilities",
        safe_divide(current_assets, current_liabilities),
        {"current_assets": current_assets, "current_liabilities": current_liabilities},
        [k for k, v in {"current_assets": current_assets, "current_liabilities": current_liabilities}.items() if v is None],
    )
    quick_assets = (current_assets - inventory) if current_assets is not None and inventory is not None else None
    if quick_assets is not None or inventory is None:
        add(
            "Quick Ratio",
            "(Current Assets - Inventory) / Current Liabilities",
            safe_divide(quick_assets, current_liabilities) if quick_assets is not None else None,
            {"quick_assets": quick_assets, "current_liabilities": current_liabilities},
            [k for k, v in {"quick_assets": quick_assets, "current_liabilities": current_liabilities}.items() if v is None],
        )
    add(
        "Free Cash Flow / Debt",
        "FCF / Total Debt",
        safe_divide(fcf, debt),
        {"fcf": fcf, "debt": debt},
        [k for k, v in {"fcf": fcf, "debt": debt}.items() if v is None],
    )
    add(
        "Cash / Debt",
        "Cash & Equivalents / Total Debt",
        safe_divide(cash, debt),
        {"cash": cash, "debt": debt},
        [k for k, v in {"cash": cash, "debt": debt}.items() if v is None],
    )
    rev_growth = None
    if revenue is not None and revenue_prior not in (None, 0):
        rev_growth = (revenue - revenue_prior) / revenue_prior
    add(
        "Revenue Growth YoY",
        "(Revenue_t - Revenue_t-1) / Revenue_t-1",
        rev_growth,
        {"revenue": revenue, "revenue_prior": revenue_prior},
        [k for k, v in {"revenue": revenue, "revenue_prior": revenue_prior}.items() if v is None],
        unit="percent",
    )
    ebitda_growth = None
    if ebitda is not None and ebitda_prior not in (None, 0):
        ebitda_growth = (ebitda - ebitda_prior) / ebitda_prior
    add(
        "EBITDA Growth YoY",
        "(EBITDA_t - EBITDA_t-1) / EBITDA_t-1",
        ebitda_growth,
        {"ebitda": ebitda, "ebitda_prior": ebitda_prior},
        [k for k, v in {"ebitda": ebitda, "ebitda_prior": ebitda_prior}.items() if v is None],
        unit="percent",
    )
    add(
        "Total Liabilities / Total Assets",
        "Total Liabilities / Total Assets",
        safe_divide(total_liabilities, total_assets),
        {"total_liabilities": total_liabilities, "total_assets": total_assets},
        [k for k, v in {"total_liabilities": total_liabilities, "total_assets": total_assets}.items() if v is None],
    )

    altman_warnings = _altman_indicators(
        working_capital=(current_assets - current_liabilities) if current_assets and current_liabilities else None,
        total_assets=total_assets,
        retained_earnings=_metric(fin, "retained_earnings"),
        ebit=operating_income,
        market_equity=_metric(fin, "market_cap"),
        total_liabilities=total_liabilities,
        revenue=revenue,
    )

    return CreditRatioSet(
        ticker=fin.ticker,
        company_name=fin.company_name,
        as_of=datetime.utcnow(),
        ratios=ratios,
        altman_warnings=altman_warnings,
    )


def _altman_indicators(
    *,
    working_capital: float | None,
    total_assets: float | None,
    retained_earnings: float | None,
    ebit: float | None,
    market_equity: float | None,
    total_liabilities: float | None,
    revenue: float | None,
) -> list[str]:
    """Lightweight Altman-style warning flags — not a full Z-score rating."""
    warnings: list[str] = []
    required = [working_capital, total_assets, retained_earnings, ebit, market_equity, total_liabilities, revenue]
    if any(v is None for v in required):
        warnings.append(
            "Insufficient data for full Altman Z-score; only indicative checks applied."
        )
        return warnings

    wc_ta = safe_divide(working_capital, total_assets)
    re_ta = safe_divide(retained_earnings, total_assets)
    ebit_ta = safe_divide(ebit, total_assets)
    if wc_ta is not None and wc_ta < 0:
        warnings.append("Negative working capital / total assets — liquidity stress indicator.")
    if re_ta is not None and re_ta < 0:
        warnings.append("Negative retained earnings / total assets — cumulative loss indicator.")
    if ebit_ta is not None and ebit_ta < 0:
        warnings.append("Negative EBIT / total assets — operating loss indicator.")
    mv_liab = safe_divide(market_equity, total_liabilities)
    if mv_liab is not None and mv_liab < 0.5:
        warnings.append("Market value of equity below half of total liabilities — leverage concern.")
    return warnings
