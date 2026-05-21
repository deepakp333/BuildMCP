"""Yahoo Finance market data and financial fallbacks via yfinance."""

from __future__ import annotations

import logging
from datetime import datetime

import yfinance as yf

from credit_review_mcp.schemas import (
    CompanyFinancials,
    DataProvenance,
    FinancialDataPoint,
    MarketData,
    RetrievalMethod,
)
from credit_review_mcp.utils import cache_key, get_cached, rate_limit, set_cached

logger = logging.getLogger(__name__)


@rate_limit("yahoo", 2.0)
def _get_ticker(symbol: str) -> yf.Ticker:
    key = cache_key("yahoo_ticker", symbol.upper())
    cached = get_cached(key)
    if cached is not None:
        return cached
    t = yf.Ticker(symbol.upper())
    set_cached(key, t)
    return t


def fetch_yahoo_market_data(ticker: str, company_name: str) -> MarketData:
    warnings: list[str] = []
    provenance = DataProvenance(
        source="Yahoo Finance",
        retrieval_method=RetrievalMethod.YAHOO_FINANCE,
        url=f"https://finance.yahoo.com/quote/{ticker.upper()}",
    )
    try:
        t = _get_ticker(ticker)
        info = t.info or {}
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        market_cap = info.get("marketCap")
        beta = info.get("beta")
        currency = info.get("currency", "USD")
        if not price:
            warnings.append("Share price unavailable from Yahoo")
        return MarketData(
            ticker=ticker.upper(),
            company_name=company_name,
            price=float(price) if price else None,
            market_cap=float(market_cap) if market_cap else None,
            beta=float(beta) if beta else None,
            currency=currency,
            provenance=provenance,
            warnings=warnings,
        )
    except Exception as exc:
        logger.warning("Yahoo market fetch failed for %s: %s", ticker, exc)
        return MarketData(
            ticker=ticker.upper(),
            company_name=company_name,
            provenance=provenance,
            warnings=[f"Yahoo market data fetch failed: {exc}"],
        )


def enrich_financials_from_yahoo(fin: CompanyFinancials) -> CompanyFinancials:
    """Fill missing SEC metrics from Yahoo financial statements where possible."""
    provenance = DataProvenance(
        source="Yahoo Finance financials",
        retrieval_method=RetrievalMethod.YAHOO_FINANCE,
    )
    try:
        t = _get_ticker(fin.ticker)
        inc = t.financials
        bal = t.balance_sheet
        cf = t.cashflow
    except Exception as exc:
        fin.warnings.append(f"Yahoo financial fallback failed: {exc}")
        return fin

    def _yf_value(df, labels: list[str]) -> float | None:
        if df is None or df.empty:
            return None
        for label in labels:
            if label in df.index:
                col = df.iloc[:, 0]
                val = col.loc[label]
                if val is not None and str(val) != "nan":
                    return float(val)
        return None

    mapping: list[tuple[str, list[str], Any]] = [
        ("revenue", ["Total Revenue", "Total Revenue"], inc),
        ("operating_income", ["Operating Income", "EBIT"], inc),
        ("net_income", ["Net Income", "Net Income Common Stockholders"], inc),
        ("ebitda", ["EBITDA", "Normalized EBITDA"], inc),
        ("total_assets", ["Total Assets"], bal),
        ("current_assets", ["Current Assets"], bal),
        ("total_liabilities", ["Total Liabilities Net Minority Interest", "Total Liab"], bal),
        ("current_liabilities", ["Current Liabilities"], bal),
        ("stockholders_equity", ["Stockholders Equity", "Total Stockholder Equity"], bal),
        ("cash_and_equivalents", ["Cash And Cash Equivalents", "Cash"], bal),
        ("long_term_debt", ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"], bal),
        ("free_cash_flow", ["Free Cash Flow"], cf),
        ("interest_expense", ["Interest Expense"], inc),
    ]

    for key, labels, df in mapping:
        if key in fin.metrics and fin.metrics[key].value is not None:
            continue
        val = _yf_value(df, labels)
        if val is not None:
            fin.metrics[key] = FinancialDataPoint(
                label=key,
                value=val,
                provenance=provenance,
            )

    if "total_debt" not in fin.metrics or fin.metrics["total_debt"].value is None:
        ltd = fin.metrics.get("long_term_debt")
        if ltd and ltd.value:
            fin.metrics["total_debt"] = FinancialDataPoint(
                label="total_debt",
                value=ltd.value,
                provenance=provenance,
            )

    if fin.metrics.get("market_cap") is None:
        try:
            cap = t.info.get("marketCap")
            if cap:
                fin.metrics["market_cap"] = FinancialDataPoint(
                    label="market_cap",
                    value=float(cap),
                    provenance=provenance,
                )
        except Exception:
            pass

    return fin
