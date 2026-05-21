"""SEC EDGAR client for submissions and XBRL companyfacts."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from credit_review_mcp.config import (
    HTTP_TIMEOUT_SECONDS,
    SEC_BASE_URL,
    SEC_RATE_LIMIT_PER_SECOND,
    SEC_USER_AGENT,
)
from credit_review_mcp.schemas import (
    CompanyFinancials,
    DataProvenance,
    FinancialDataPoint,
    RetrievalMethod,
)
from credit_review_mcp.utils import cache_key, get_cached, normalize_cik, rate_limit, set_cached

logger = logging.getLogger(__name__)

# Common US-GAAP tags mapped to internal metric keys
TAG_MAP = {
    "Revenues": "revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "SalesRevenueNet": "revenue",
    "OperatingIncomeLoss": "operating_income",
    "NetIncomeLoss": "net_income",
    "Assets": "total_assets",
    "AssetsCurrent": "current_assets",
    "Liabilities": "total_liabilities",
    "LiabilitiesCurrent": "current_liabilities",
    "StockholdersEquity": "stockholders_equity",
    "LongTermDebt": "long_term_debt",
    "LongTermDebtNoncurrent": "long_term_debt",
    "DebtCurrent": "short_term_debt",
    "InterestExpense": "interest_expense",
    "CashAndCashEquivalentsAtCarryingValue": "cash_and_equivalents",
    "InventoryNet": "inventory",
    "AccountsReceivableNetCurrent": "receivables",
    "RetainedEarningsAccumulatedDeficit": "retained_earnings",
    "Goodwill": "goodwill",
    "DepreciationDepletionAndAmortization": "depreciation_amortization",
    "PaymentsToAcquirePropertyPlantAndEquipment": "capex",
}


@rate_limit("sec", SEC_RATE_LIMIT_PER_SECOND)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _sec_get(path: str) -> dict[str, Any]:
    url = f"{SEC_BASE_URL}{path}"
    key = cache_key("sec", path)
    cached = get_cached(key)
    if cached is not None:
        return cached

    headers = {
        "User-Agent": SEC_USER_AGENT,
        "Accept": "application/json",
    }
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    set_cached(key, data)
    return data


def fetch_company_submissions(cik: str) -> dict[str, Any]:
    norm = normalize_cik(cik)
    if not norm:
        raise ValueError(f"Invalid CIK: {cik}")
    return _sec_get(f"/submissions/CIK{norm}.json")


def fetch_company_facts(cik: str) -> dict[str, Any]:
    norm = normalize_cik(cik)
    if not norm:
        raise ValueError(f"Invalid CIK: {cik}")
    return _sec_get(f"/api/xbrl/companyfacts/CIK{norm}.json")


def _latest_annual_value(facts: dict[str, Any], tag: str) -> tuple[float | None, str | None]:
    """Extract most recent annual (FY) USD value for a GAAP tag."""
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    entry = us_gaap.get(tag)
    if not entry:
        return None, None
    units = entry.get("units", {})
    usd = units.get("USD") or units.get("usd") or []
    if not usd:
        return None, None
    # Prefer 10-K / FY filings
    annual = [u for u in usd if u.get("form") in ("10-K", "10-K/A") or u.get("fp") == "FY"]
    pool = annual if annual else usd
    pool_sorted = sorted(pool, key=lambda x: x.get("end", ""), reverse=True)
    if not pool_sorted:
        return None, None
    latest = pool_sorted[0]
    val = latest.get("val")
    return (float(val) if val is not None else None, latest.get("end"))


def fetch_sec_financials(
    *,
    ticker: str,
    cik: str | None,
    company_name: str,
) -> CompanyFinancials:
    """Fetch and normalize SEC XBRL companyfacts into CompanyFinancials."""
    warnings: list[str] = []
    provenance = DataProvenance(
        source="SEC EDGAR companyfacts",
        retrieval_method=RetrievalMethod.SEC_API,
        url=f"{SEC_BASE_URL}/api/xbrl/companyfacts/",
        notes=f"User-Agent: {SEC_USER_AGENT}",
    )

    if not cik:
        warnings.append("CIK not provided — SEC financials unavailable")
        return CompanyFinancials(
            ticker=ticker,
            company_name=company_name,
            metrics={},
            warnings=warnings,
        )

    try:
        raw = fetch_company_facts(cik)
    except Exception as exc:
        logger.warning("SEC fetch failed for %s: %s", ticker, exc)
        warnings.append(f"SEC companyfacts fetch failed: {exc}")
        return CompanyFinancials(
            ticker=ticker,
            cik=normalize_cik(cik),
            company_name=company_name,
            metrics={},
            warnings=warnings,
        )

    metrics: dict[str, FinancialDataPoint] = {}
    raw_tags: dict[str, Any] = {}
    fiscal_year: int | None = None

    for gaap_tag, metric_key in TAG_MAP.items():
        value, period_end = _latest_annual_value(raw, gaap_tag)
        if value is None:
            continue
        raw_tags[gaap_tag] = value
        if period_end and fiscal_year is None:
            try:
                fiscal_year = int(period_end[:4])
            except ValueError:
                pass
        metrics[metric_key] = FinancialDataPoint(
            label=metric_key,
            value=value,
            period=period_end,
            provenance=provenance,
        )

    # Derived EBITDA proxy: Operating Income + D&A (simplified)
    op = metrics.get("operating_income")
    da = metrics.get("depreciation_amortization")
    if op and op.value is not None:
        ebitda_val = op.value + (da.value if da and da.value else 0)
        metrics["ebitda"] = FinancialDataPoint(
            label="ebitda",
            value=ebitda_val,
            period=op.period,
            provenance=provenance,
            unit="USD (proxy: OpInc + D&A)",
        )

    # Total debt proxy
    ltd = metrics.get("long_term_debt")
    std = metrics.get("short_term_debt")
    if ltd or std:
        total_debt = (ltd.value if ltd and ltd.value else 0) + (std.value if std and std.value else 0)
        metrics["total_debt"] = FinancialDataPoint(
            label="total_debt",
            value=total_debt,
            provenance=provenance,
        )

    # Prior year revenue / EBITDA for growth
    for tag, key in (("Revenues", "revenue_prior_year"),):
        us_gaap = raw.get("facts", {}).get("us-gaap", {})
        entry = us_gaap.get(tag) or us_gaap.get("RevenueFromContractWithCustomerExcludingAssessedTax")
        if entry:
            usd = entry.get("units", {}).get("USD", [])
            annual = sorted(
                [u for u in usd if u.get("form") in ("10-K", "10-K/A") or u.get("fp") == "FY"],
                key=lambda x: x.get("end", ""),
                reverse=True,
            )
            if len(annual) >= 2:
                prior_val = annual[1].get("val")
                if prior_val is not None:
                    metrics[key] = FinancialDataPoint(
                        label=key,
                        value=float(prior_val),
                        period=annual[1].get("end"),
                        provenance=provenance,
                    )

    if not metrics:
        warnings.append("No recognized US-GAAP tags found in SEC companyfacts")

    return CompanyFinancials(
        ticker=ticker,
        cik=normalize_cik(cik),
        company_name=company_name,
        fiscal_year=fiscal_year,
        metrics=metrics,
        raw_tags=raw_tags,
        warnings=warnings,
    )


def resolve_cik_from_submissions(ticker: str, company_name: str) -> str | None:
    """Best-effort CIK lookup via SEC submissions search is not available without ticker index;
    Returns None — callers should supply CIK in universe CSV."""
    return None
