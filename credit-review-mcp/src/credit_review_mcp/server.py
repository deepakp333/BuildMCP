"""MCP server exposing credit review tools, resources, and prompts."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from credit_review_mcp.config import SAMPLE_DATA_DIR
from credit_review_mcp.news_client import assess_news_sentiment, collect_trusted_news
from credit_review_mcp.pdf_export import export_credit_memo_pdf
from credit_review_mcp.utils import setup_logging
from credit_review_mcp.workflow import (
    load_company_universe,
    resolve_company_identifiers,
    review_single_company,
    run_demo_credit_review,
)
from credit_review_mcp.sec_client import fetch_sec_financials
from credit_review_mcp.yahoo_client import fetch_yahoo_market_data
from credit_review_mcp.ratios import calculate_credit_ratios
from credit_review_mcp.camel import run_camel_assessment
from credit_review_mcp.memo import generate_credit_memo

mcp = FastMCP(
    "credit-review-mcp",
    instructions=(
        "Demo MCP server for credit analyst workflows. "
        "Deterministic ratios and CAMEL scoring; optional LLM for memo narrative only. "
        "Not a rating action or credit approval."
    ),
)


@mcp.tool()
def load_company_universe_tool(
    csv_path: str | None = None,
    website_url: str | None = None,
    max_companies: int = 5,
) -> dict:
    """Load company universe from CSV or optional HTML table URL (max 5 by default)."""
    universe = load_company_universe(csv_path, website_url, max_companies)
    return universe.model_dump(mode="json")


@mcp.tool()
def resolve_company_identifiers_tool(companies: list[dict]) -> list[dict]:
    """Normalize tickers and CIKs for a list of company records."""
    from credit_review_mcp.schemas import CompanyRecord

    records = [CompanyRecord.model_validate(c) for c in companies]
    resolved = resolve_company_identifiers(records)
    return [r.model_dump(mode="json") for r in resolved]


@mcp.tool()
def fetch_sec_financials_tool(ticker: str, cik: str | None, company_name: str) -> dict:
    """Fetch SEC EDGAR XBRL companyfacts for a company."""
    fin = fetch_sec_financials(ticker=ticker, cik=cik, company_name=company_name)
    return fin.model_dump(mode="json")


@mcp.tool()
def fetch_yahoo_market_data_tool(ticker: str, company_name: str) -> dict:
    """Fetch Yahoo Finance market data (price, cap, beta)."""
    data = fetch_yahoo_market_data(ticker, company_name)
    return data.model_dump(mode="json")


@mcp.tool()
def calculate_credit_ratios_tool(financials: dict) -> dict:
    """Calculate deterministic credit ratios from normalized financials."""
    from credit_review_mcp.schemas import CompanyFinancials

    fin = CompanyFinancials.model_validate(financials)
    ratios = calculate_credit_ratios(fin)
    return ratios.model_dump(mode="json")


@mcp.tool()
def collect_trusted_news_tool(ticker: str, company_name: str, limit: int = 5) -> dict:
    """Collect top trusted news items (Yahoo/NewsAPI or mock demo)."""
    news = collect_trusted_news(ticker, company_name, limit)
    return news.model_dump(mode="json")


@mcp.tool()
def assess_news_sentiment_tool(articles: list[dict]) -> list[dict]:
    """Apply deterministic finance-aware keyword sentiment to articles."""
    from credit_review_mcp.schemas import NewsArticle

    parsed = [NewsArticle.model_validate(a) for a in articles]
    scored = assess_news_sentiment(parsed)
    return [a.model_dump(mode="json") for a in scored]


@mcp.tool()
def run_camel_assessment_tool(
    ticker: str,
    company_name: str,
    financials: dict | None = None,
    ratios: dict | None = None,
    market_data: dict | None = None,
    news: dict | None = None,
) -> dict:
    """Run adapted CAMEL assessment (scores 1=strong to 5=weak)."""
    from credit_review_mcp.schemas import CompanyFinancials, CreditRatioSet, MarketData, NewsCollection

    assessment = run_camel_assessment(
        fin=CompanyFinancials.model_validate(financials) if financials else None,
        ratios=CreditRatioSet.model_validate(ratios) if ratios else None,
        market=MarketData.model_validate(market_data) if market_data else None,
        news=NewsCollection.model_validate(news) if news else None,
        company_name=company_name,
        ticker=ticker,
    )
    return assessment.model_dump(mode="json")


@mcp.tool()
def generate_credit_memo_tool(
    company: dict,
    financials: dict | None = None,
    market_data: dict | None = None,
    ratios: dict | None = None,
    news: dict | None = None,
    camel: dict | None = None,
) -> dict:
    """Generate draft credit memo (deterministic + optional LLM narrative)."""
    from credit_review_mcp.schemas import (
        CamelAssessment,
        CompanyFinancials,
        CompanyRecord,
        CreditRatioSet,
        MarketData,
        NewsCollection,
    )

    memo = generate_credit_memo(
        CompanyRecord.model_validate(company),
        CompanyFinancials.model_validate(financials) if financials else None,
        MarketData.model_validate(market_data) if market_data else None,
        CreditRatioSet.model_validate(ratios) if ratios else None,
        NewsCollection.model_validate(news) if news else None,
        CamelAssessment.model_validate(camel) if camel else None,
    )
    return memo.model_dump(mode="json")


@mcp.tool()
def export_credit_memo_pdf_tool(memo: dict, output_dir: str | None = None) -> str:
    """Export credit memo to PDF; returns file path."""
    from credit_review_mcp.schemas import CreditMemo

    path = export_credit_memo_pdf(
        CreditMemo.model_validate(memo),
        Path(output_dir) if output_dir else None,
    )
    return path


@mcp.tool()
def run_demo_credit_review_tool(
    csv_path: str | None = None,
    website_url: str | None = None,
    max_companies: int = 5,
) -> dict:
    """Run full demo credit review pipeline for universe (default sample CSV)."""
    result = run_demo_credit_review(csv_path, website_url, max_companies)
    return result.model_dump(mode="json")


@mcp.resource("credit://schema/company-input")
def schema_company_input() -> str:
    return json.dumps(
        {
            "description": "Company universe input schema",
            "csv_columns": ["company_name", "ticker", "cik", "sector"],
            "max_companies_default": 5,
            "example": {
                "company_name": "Apple Inc.",
                "ticker": "AAPL",
                "cik": "0000320193",
                "sector": "Technology",
            },
        },
        indent=2,
    )


@mcp.resource("credit://schema/credit-ratios")
def schema_credit_ratios() -> str:
    return json.dumps(
        {
            "ratios": [
                {"name": "Debt / EBITDA", "formula": "Total Debt / EBITDA"},
                {"name": "Debt / Equity", "formula": "Total Debt / Stockholders' Equity"},
                {"name": "Interest Coverage", "formula": "EBITDA / Interest Expense"},
                {"name": "EBITDA Margin", "formula": "EBITDA / Revenue"},
                {"name": "Operating Margin", "formula": "Operating Income / Revenue"},
                {"name": "Current Ratio", "formula": "Current Assets / Current Liabilities"},
                {"name": "Quick Ratio", "formula": "(Current Assets - Inventory) / Current Liabilities"},
                {"name": "Free Cash Flow / Debt", "formula": "FCF / Total Debt"},
                {"name": "Cash / Debt", "formula": "Cash / Total Debt"},
                {"name": "Revenue Growth YoY", "formula": "(Rev_t - Rev_t-1) / Rev_t-1"},
                {"name": "EBITDA Growth YoY", "formula": "(EBITDA_t - EBITDA_t-1) / EBITDA_t-1"},
                {"name": "Total Liabilities / Total Assets", "formula": "Total Liabilities / Total Assets"},
            ],
            "notes": "All calculations are deterministic; Altman Z-score not claimed in full.",
        },
        indent=2,
    )


@mcp.resource("credit://framework/camel")
def resource_camel_framework() -> str:
    return json.dumps(
        {
            "framework": "Adapted CAMEL for public companies",
            "components": [
                {
                    "name": "Capital Adequacy",
                    "focus": "Leverage, debt/equity, retained earnings, capitalization",
                },
                {
                    "name": "Asset Quality",
                    "focus": "Working capital, receivables/inventory, intangibles",
                },
                {
                    "name": "Management Capability",
                    "focus": "Governance/news red flags, filing timeliness",
                },
                {
                    "name": "Earnings",
                    "focus": "Revenue growth, margins, EBITDA, cash generation",
                },
                {
                    "name": "Liquidity",
                    "focus": "Current ratio, cash, FCF vs debt",
                },
            ],
            "scoring": "1 (strong) to 5 (weak); rules-based demo scorer",
        },
        indent=2,
    )


@mcp.resource("credit://demo/sample-companies")
def resource_sample_companies() -> str:
    path = SAMPLE_DATA_DIR / "companies.csv"
    return path.read_text(encoding="utf-8")


@mcp.prompt()
def credit_memo_prompt(ticker: str = "AAPL", company_name: str = "Apple Inc.") -> str:
    return (
        f"Draft a concise credit memo for {company_name} ({ticker}) using MCP tools: "
        "fetch_sec_financials, fetch_yahoo_market_data, calculate_credit_ratios, "
        "collect_trusted_news, run_camel_assessment, generate_credit_memo, export_credit_memo_pdf. "
        "Use only tool-returned data. Mark output as draft for analyst review."
    )


@mcp.prompt()
def credit_review_workflow_prompt() -> str:
    return (
        "Execute the demo credit review workflow:\n"
        "1. load_company_universe from sample_data/companies.csv (max 5)\n"
        "2. resolve_company_identifiers\n"
        "3. For each company: SEC financials, Yahoo market data, ratios, news, CAMEL\n"
        "4. generate_credit_memo and export_credit_memo_pdf\n"
        "Or call run_demo_credit_review for the full pipeline.\n"
        "Never treat output as a rating action or approval."
    )


@mcp.prompt()
def analyst_challenge_prompt(claim: str = "Leverage is acceptable") -> str:
    return (
        f"Challenge this credit claim with evidence from tool outputs only: '{claim}'.\n"
        "List supporting metrics, missing data, and alternative interpretations.\n"
        "Require analyst sign-off before any credit decision."
    )


def main() -> None:
    setup_logging()
    mcp.run()


if __name__ == "__main__":
    main()
