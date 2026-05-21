"""Unit tests for CAMEL scoring."""

from credit_review_mcp.camel import run_camel_assessment
from credit_review_mcp.ratios import calculate_credit_ratios
from credit_review_mcp.schemas import CompanyFinancials, DataProvenance, FinancialDataPoint, RetrievalMethod
from credit_review_mcp.news_client import MockNewsAdapter


def _build_fixtures():
    prov = DataProvenance(source="test", retrieval_method=RetrievalMethod.DETERMINISTIC)
    metrics = {
        "total_debt": FinancialDataPoint(label="total_debt", value=500.0, provenance=prov),
        "ebitda": FinancialDataPoint(label="ebitda", value=100.0, provenance=prov),
        "stockholders_equity": FinancialDataPoint(label="equity", value=400.0, provenance=prov),
        "revenue": FinancialDataPoint(label="revenue", value=1000.0, provenance=prov),
        "operating_income": FinancialDataPoint(label="op", value=80.0, provenance=prov),
        "current_assets": FinancialDataPoint(label="ca", value=200.0, provenance=prov),
        "current_liabilities": FinancialDataPoint(label="cl", value=150.0, provenance=prov),
        "cash_and_equivalents": FinancialDataPoint(label="cash", value=50.0, provenance=prov),
        "free_cash_flow": FinancialDataPoint(label="fcf", value=40.0, provenance=prov),
        "total_liabilities": FinancialDataPoint(label="tl", value=600.0, provenance=prov),
        "total_assets": FinancialDataPoint(label="ta", value=1000.0, provenance=prov),
        "revenue_prior_year": FinancialDataPoint(label="rev_py", value=900.0, provenance=prov),
        "interest_expense": FinancialDataPoint(label="int", value=10.0, provenance=prov),
    }
    fin = CompanyFinancials(ticker="TST", company_name="Test Corp", metrics=metrics)
    ratios = calculate_credit_ratios(fin)
    news = MockNewsAdapter().fetch("TST", "Test Corp", 5)
    return fin, ratios, news


def test_camel_has_five_components():
    fin, ratios, news = _build_fixtures()
    assessment = run_camel_assessment(
        fin=fin,
        ratios=ratios,
        market=None,
        news=news,
        company_name="Test Corp",
        ticker="TST",
    )
    assert len(assessment.components) == 5
    names = {c.component for c in assessment.components}
    assert "Capital Adequacy" in names
    assert "Liquidity" in names


def test_camel_scores_in_range():
    fin, ratios, news = _build_fixtures()
    assessment = run_camel_assessment(
        fin=fin,
        ratios=ratios,
        market=None,
        news=news,
        company_name="Test Corp",
        ticker="TST",
    )
    for c in assessment.components:
        assert 1 <= c.score <= 5
