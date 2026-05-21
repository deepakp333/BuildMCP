"""Unit tests for credit ratio calculations."""

from credit_review_mcp.ratios import calculate_credit_ratios
from credit_review_mcp.schemas import CompanyFinancials, DataProvenance, FinancialDataPoint, RetrievalMethod


def _fin() -> CompanyFinancials:
    prov = DataProvenance(source="test", retrieval_method=RetrievalMethod.DETERMINISTIC)
    metrics = {
        "total_debt": FinancialDataPoint(label="total_debt", value=100.0, provenance=prov),
        "ebitda": FinancialDataPoint(label="ebitda", value=50.0, provenance=prov),
        "stockholders_equity": FinancialDataPoint(label="stockholders_equity", value=200.0, provenance=prov),
        "interest_expense": FinancialDataPoint(label="interest_expense", value=5.0, provenance=prov),
        "revenue": FinancialDataPoint(label="revenue", value=500.0, provenance=prov),
        "operating_income": FinancialDataPoint(label="operating_income", value=60.0, provenance=prov),
        "current_assets": FinancialDataPoint(label="current_assets", value=150.0, provenance=prov),
        "current_liabilities": FinancialDataPoint(label="current_liabilities", value=100.0, provenance=prov),
        "inventory": FinancialDataPoint(label="inventory", value=20.0, provenance=prov),
        "cash_and_equivalents": FinancialDataPoint(label="cash", value=40.0, provenance=prov),
        "free_cash_flow": FinancialDataPoint(label="fcf", value=30.0, provenance=prov),
        "total_liabilities": FinancialDataPoint(label="tl", value=300.0, provenance=prov),
        "total_assets": FinancialDataPoint(label="ta", value=800.0, provenance=prov),
        "revenue_prior_year": FinancialDataPoint(label="rev_py", value=450.0, provenance=prov),
        "ebitda_prior_year": FinancialDataPoint(label="ebitda_py", value=45.0, provenance=prov),
        "retained_earnings": FinancialDataPoint(label="re", value=120.0, provenance=prov),
        "market_cap": FinancialDataPoint(label="mcap", value=1000.0, provenance=prov),
    }
    return CompanyFinancials(
        ticker="TEST",
        company_name="Test Co",
        metrics=metrics,
    )


def test_debt_ebitda():
    result = calculate_credit_ratios(_fin())
    by_name = {r.name: r for r in result.ratios}
    assert by_name["Debt / EBITDA"].value == 2.0


def test_interest_coverage():
    result = calculate_credit_ratios(_fin())
    by_name = {r.name: r for r in result.ratios}
    assert by_name["Interest Coverage"].value == 10.0


def test_revenue_growth():
    result = calculate_credit_ratios(_fin())
    by_name = {r.name: r for r in result.ratios}
    growth = by_name["Revenue Growth YoY"].value
    assert growth is not None
    assert abs(growth - (50 / 450)) < 0.001
