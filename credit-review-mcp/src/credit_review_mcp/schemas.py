"""Pydantic models for structured credit review inputs and outputs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RetrievalMethod(str, Enum):
    SEC_API = "sec_api"
    YAHOO_FINANCE = "yahoo_finance"
    MOCK_DEMO = "mock_demo"
    HTML_TABLE = "html_table"
    CSV_FILE = "csv_file"
    DETERMINISTIC = "deterministic"
    LLM_SYNTHESIS = "llm_synthesis"


class DataProvenance(BaseModel):
    source: str
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    retrieval_method: RetrievalMethod
    url: str | None = None
    notes: str | None = None


class CompanyRecord(BaseModel):
    company_name: str
    ticker: str | None = None
    cik: str | None = None
    sector: str | None = None


class CompanyUniverse(BaseModel):
    companies: list[CompanyRecord]
    source: DataProvenance
    max_companies: int = 5


class FinancialDataPoint(BaseModel):
    label: str
    value: float | None
    unit: str = "USD"
    period: str | None = None
    provenance: DataProvenance


class CompanyFinancials(BaseModel):
    ticker: str
    cik: str | None = None
    company_name: str
    fiscal_year: int | None = None
    metrics: dict[str, FinancialDataPoint] = Field(default_factory=dict)
    raw_tags: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class MarketData(BaseModel):
    ticker: str
    company_name: str
    price: float | None = None
    market_cap: float | None = None
    beta: float | None = None
    currency: str = "USD"
    as_of: datetime = Field(default_factory=datetime.utcnow)
    provenance: DataProvenance
    warnings: list[str] = Field(default_factory=list)


class CreditRatio(BaseModel):
    name: str
    formula: str
    value: float | None
    unit: str = "ratio"
    interpretation: str | None = None
    inputs_used: dict[str, float | None] = Field(default_factory=dict)
    missing_inputs: list[str] = Field(default_factory=list)
    provenance: DataProvenance | None = None


class CreditRatioSet(BaseModel):
    ticker: str
    company_name: str
    as_of: datetime = Field(default_factory=datetime.utcnow)
    ratios: list[CreditRatio] = Field(default_factory=list)
    altman_warnings: list[str] = Field(default_factory=list)


class NewsArticle(BaseModel):
    title: str
    source: str
    published_at: datetime
    url: str
    summary: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    sentiment_score: float = Field(ge=-1.0, le=1.0, default=0.0)
    is_mock: bool = False
    provenance: DataProvenance


class NewsCollection(BaseModel):
    ticker: str
    articles: list[NewsArticle] = Field(default_factory=list)
    retrieval_mode: str = "mock_demo"


class CamelComponentScore(BaseModel):
    component: str
    score: int = Field(ge=1, le=5, description="1=strong, 5=weak")
    rationale: str
    supporting_metrics: dict[str, float | str | None] = Field(default_factory=dict)
    confidence: str = "medium"
    missing_data_warnings: list[str] = Field(default_factory=list)


class CamelAssessment(BaseModel):
    ticker: str
    company_name: str
    as_of: datetime = Field(default_factory=datetime.utcnow)
    components: list[CamelComponentScore] = Field(default_factory=list)
    overall_score: float | None = None
    overall_rationale: str = ""


class MemoSection(BaseModel):
    title: str
    content: str


class CreditMemo(BaseModel):
    ticker: str
    company_name: str
    as_of_date: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str
    sections: list[MemoSection] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    llm_used: bool = False
    token_usage: dict[str, int] | None = None


class CompanyReviewResult(BaseModel):
    company: CompanyRecord
    financials: CompanyFinancials | None = None
    market_data: MarketData | None = None
    ratios: CreditRatioSet | None = None
    news: NewsCollection | None = None
    camel: CamelAssessment | None = None
    memo: CreditMemo | None = None
    pdf_path: str | None = None
    run_json_path: str | None = None
    errors: list[str] = Field(default_factory=list)


class DemoReviewResult(BaseModel):
    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    companies_processed: int
    results: list[CompanyReviewResult] = Field(default_factory=list)
    summary: str = ""
