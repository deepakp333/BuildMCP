"""End-to-end credit review workflow orchestration."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
import httpx
import pandas as pd
from bs4 import BeautifulSoup

from credit_review_mcp.camel import run_camel_assessment
from credit_review_mcp.config import RUNS_DIR, SAMPLE_DATA_DIR
from credit_review_mcp.memo import generate_credit_memo
from credit_review_mcp.news_client import collect_trusted_news
from credit_review_mcp.pdf_export import export_credit_memo_pdf
from credit_review_mcp.ratios import calculate_credit_ratios
from credit_review_mcp.schemas import (
    CompanyRecord,
    CompanyReviewResult,
    CompanyUniverse,
    DataProvenance,
    DemoReviewResult,
    RetrievalMethod,
)
from credit_review_mcp.sec_client import fetch_sec_financials
from credit_review_mcp.utils import normalize_cik, run_id, save_json, setup_logging
from credit_review_mcp.yahoo_client import enrich_financials_from_yahoo, fetch_yahoo_market_data

logger = logging.getLogger(__name__)


def load_company_universe(
    csv_path: str | None = None,
    website_url: str | None = None,
    max_companies: int = 5,
) -> CompanyUniverse:
    companies: list[CompanyRecord] = []
    source_method = RetrievalMethod.CSV_FILE
    source_name = "local CSV"

    if csv_path:
        path = Path(csv_path)
        if not path.is_absolute():
            path = Path(csv_path)
        if not path.exists():
            alt = SAMPLE_DATA_DIR / "companies.csv"
            if alt.exists():
                path = alt
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            companies.append(
                CompanyRecord(
                    company_name=str(row.get("company_name", row.get("name", ""))),
                    ticker=str(row["ticker"]).strip() if pd.notna(row.get("ticker")) else None,
                    cik=str(row["cik"]).strip() if pd.notna(row.get("cik")) else None,
                    sector=str(row["sector"]).strip() if pd.notna(row.get("sector")) else None,
                )
            )
    elif website_url:
        companies = _parse_html_table(website_url)
        source_method = RetrievalMethod.HTML_TABLE
        source_name = website_url
    else:
        default_csv = SAMPLE_DATA_DIR / "companies.csv"
        return load_company_universe(str(default_csv), None, max_companies)

    companies = companies[:max_companies]
    return CompanyUniverse(
        companies=companies,
        max_companies=max_companies,
        source=DataProvenance(
            source=source_name,
            retrieval_method=source_method,
            url=csv_path or website_url,
        ),
    )


def _parse_html_table(url: str) -> list[CompanyRecord]:
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers={"User-Agent": "CreditReviewDemo/0.1"})
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table")
    if not table:
        return []
    rows = table.find_all("tr")
    if len(rows) < 2:
        return []
    headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
    companies: list[CompanyRecord] = []
    for tr in rows[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if not cells:
            continue
        row_map = dict(zip(headers, cells, strict=False))
        companies.append(
            CompanyRecord(
                company_name=row_map.get("company_name") or row_map.get("name", ""),
                ticker=row_map.get("ticker"),
                cik=row_map.get("cik"),
                sector=row_map.get("sector"),
            )
        )
    return companies


def resolve_company_identifiers(companies: list[CompanyRecord]) -> list[CompanyRecord]:
    resolved: list[CompanyRecord] = []
    for c in companies:
        cik = normalize_cik(c.cik) if c.cik else None
        ticker = c.ticker.upper().strip() if c.ticker else None
        resolved.append(
            CompanyRecord(
                company_name=c.company_name,
                ticker=ticker,
                cik=cik,
                sector=c.sector,
            )
        )
    return resolved


def review_single_company(company: CompanyRecord) -> CompanyReviewResult:
    result = CompanyReviewResult(company=company)
    ticker = company.ticker or "UNKNOWN"
    errors: list[str] = []

    try:
        fin = fetch_sec_financials(
            ticker=ticker,
            cik=company.cik,
            company_name=company.company_name,
        )
        fin = enrich_financials_from_yahoo(fin)
        result.financials = fin
    except Exception as exc:
        errors.append(f"Financials: {exc}")
        logger.exception("Financials failed for %s", ticker)

    try:
        result.market_data = fetch_yahoo_market_data(ticker, company.company_name)
        if result.financials and result.market_data and result.market_data.market_cap:
            from credit_review_mcp.schemas import FinancialDataPoint, RetrievalMethod

            result.financials.metrics["market_cap"] = FinancialDataPoint(
                label="market_cap",
                value=result.market_data.market_cap,
                provenance=result.market_data.provenance,
            )
    except Exception as exc:
        errors.append(f"Market data: {exc}")

    ratios = None
    if result.financials:
        try:
            ratios = calculate_credit_ratios(result.financials)
            result.ratios = ratios
        except Exception as exc:
            errors.append(f"Ratios: {exc}")

    try:
        news = collect_trusted_news(ticker, company.company_name, limit=5)
        result.news = news
    except Exception as exc:
        errors.append(f"News: {exc}")

    try:
        camel = run_camel_assessment(
            fin=result.financials,
            ratios=ratios,
            market=result.market_data,
            news=result.news,
            company_name=company.company_name,
            ticker=ticker,
        )
        result.camel = camel
    except Exception as exc:
        errors.append(f"CAMEL: {exc}")

    try:
        memo = generate_credit_memo(
            company,
            result.financials,
            result.market_data,
            ratios,
            result.news,
            result.camel,
        )
        result.memo = memo
        pdf_path = export_credit_memo_pdf(memo)
        result.pdf_path = pdf_path
    except Exception as exc:
        errors.append(f"Memo/PDF: {exc}")

    rid = run_id()
    run_path = RUNS_DIR / f"run_{ticker}_{rid}.json"
    payload = result.model_dump(mode="json")
    save_json(run_path, payload)
    result.run_json_path = str(run_path)
    result.errors = errors
    return result


def run_demo_credit_review(
    csv_path: str | None = None,
    website_url: str | None = None,
    max_companies: int = 5,
) -> DemoReviewResult:
    setup_logging()
    started = datetime.utcnow()
    rid = run_id()
    universe = load_company_universe(csv_path, website_url, max_companies)
    companies = resolve_company_identifiers(universe.companies)
    results: list[CompanyReviewResult] = []
    for company in companies:
        logger.info("Reviewing %s (%s)", company.company_name, company.ticker)
        results.append(review_single_company(company))

    completed = datetime.utcnow()
    demo = DemoReviewResult(
        run_id=rid,
        started_at=started,
        completed_at=completed,
        companies_processed=len(results),
        results=results,
        summary=(
            f"Processed {len(results)} companies. "
            f"PDFs: {sum(1 for r in results if r.pdf_path)}. "
            "Draft memos require analyst review."
        ),
    )
    save_json(RUNS_DIR / f"demo_{rid}.json", demo.model_dump(mode="json"))
    return demo
