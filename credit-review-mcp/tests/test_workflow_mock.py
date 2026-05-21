"""Workflow tests with mocked external calls."""

from pathlib import Path
from unittest.mock import patch

from credit_review_mcp.schemas import CompanyFinancials, DataProvenance, FinancialDataPoint, RetrievalMethod
from credit_review_mcp.workflow import load_company_universe, run_demo_credit_review


SAMPLE_CSV = Path(__file__).resolve().parents[1] / "sample_data" / "companies.csv"


def _mock_financials(ticker: str, cik: str | None, company_name: str) -> CompanyFinancials:
    prov = DataProvenance(source="mock", retrieval_method=RetrievalMethod.MOCK_DEMO)
    return CompanyFinancials(
        ticker=ticker,
        cik=cik,
        company_name=company_name,
        metrics={
            "revenue": FinancialDataPoint(label="revenue", value=1e9, provenance=prov),
            "ebitda": FinancialDataPoint(label="ebitda", value=2e8, provenance=prov),
            "total_debt": FinancialDataPoint(label="debt", value=5e8, provenance=prov),
            "stockholders_equity": FinancialDataPoint(label="eq", value=8e8, provenance=prov),
            "current_assets": FinancialDataPoint(label="ca", value=4e8, provenance=prov),
            "current_liabilities": FinancialDataPoint(label="cl", value=3e8, provenance=prov),
            "cash_and_equivalents": FinancialDataPoint(label="cash", value=1e8, provenance=prov),
            "operating_income": FinancialDataPoint(label="op", value=1.5e8, provenance=prov),
            "interest_expense": FinancialDataPoint(label="int", value=2e7, provenance=prov),
            "free_cash_flow": FinancialDataPoint(label="fcf", value=8e7, provenance=prov),
            "total_liabilities": FinancialDataPoint(label="tl", value=9e8, provenance=prov),
            "total_assets": FinancialDataPoint(label="ta", value=2e9, provenance=prov),
            "revenue_prior_year": FinancialDataPoint(label="rpy", value=9e8, provenance=prov),
        },
    )


@patch("credit_review_mcp.workflow.fetch_yahoo_market_data")
@patch("credit_review_mcp.workflow.enrich_financials_from_yahoo")
@patch("credit_review_mcp.workflow.fetch_sec_financials")
def test_load_universe(mock_sec, mock_enrich, mock_yahoo):
    universe = load_company_universe(str(SAMPLE_CSV), max_companies=3)
    assert len(universe.companies) == 3
    assert universe.companies[0].ticker == "AAPL"


@patch("credit_review_mcp.workflow.fetch_yahoo_market_data")
@patch("credit_review_mcp.workflow.enrich_financials_from_yahoo")
@patch("credit_review_mcp.workflow.fetch_sec_financials")
def test_demo_review_mocked(mock_sec, mock_enrich, mock_yahoo):
    from credit_review_mcp.schemas import MarketData

    mock_sec.side_effect = _mock_financials
    mock_enrich.side_effect = lambda fin: fin
    mock_yahoo.return_value = MarketData(
        ticker="AAPL",
        company_name="Apple Inc.",
        price=180.0,
        market_cap=2e12,
        beta=1.2,
        provenance=DataProvenance(source="mock", retrieval_method=RetrievalMethod.MOCK_DEMO),
    )

    result = run_demo_credit_review(str(SAMPLE_CSV), max_companies=1)
    assert result.companies_processed == 1
    assert result.results[0].memo is not None
    assert result.results[0].pdf_path is not None
    assert Path(result.results[0].pdf_path).exists()
