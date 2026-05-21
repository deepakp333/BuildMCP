"""Pydantic schemas for the Credit Review Platform."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Signal(str, Enum):
    STRONG = "strong"
    ADEQUATE = "adequate"
    WATCH = "watch"
    WEAK = "weak"


class ResolvedEntity(BaseModel):
    id: str
    name: str
    entity_type: EntityType
    ticker: str | None = None
    cik: str | None = None
    cert_number: str | None = None
    charter_number: str | None = None
    match_score: float = Field(ge=0, le=100)


class MetricPoint(BaseModel):
    period: str
    value: float


class MetricSeries(BaseModel):
    key: str
    label: str
    unit: str
    points: list[MetricPoint]
    trend_slope: float | None = None
    trend_direction: Literal["up", "down", "flat"] | None = None


class RiskFlag(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    message: str
    metric_key: str | None = None


class CamelsScore(BaseModel):
    capital: float
    asset_quality: float
    management: float
    earnings: float
    liquidity: float
    sensitivity: float
    composite: float


class FilingRecord(BaseModel):
    form_type: str
    filed_date: str
    accession_number: str
    description: str
    url: str | None = None


class NewsArticle(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    sentiment: Literal["positive", "neutral", "negative"]


class LitigationRecord(BaseModel):
    case_name: str
    court: str
    date_filed: str
    docket_number: str
    url: str | None = None


class TradeSignal(BaseModel):
    payment_index: float
    delinquency_rate: float
    trade_credit_rating: str
    supplier_count: int


class ExcelEntityRow(BaseModel):
    name: str
    entity_type: EntityType
    ticker: str | None = None
    cert_number: str | None = None
    notes: str | None = None


class PublicReviewResult(BaseModel):
    entity: ResolvedEntity
    signal: Signal
    metrics: list[MetricSeries]
    camels: CamelsScore | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    filings: list[FilingRecord] = Field(default_factory=list)
    news: list[NewsArticle] = Field(default_factory=list)
    commentary: str = ""


class PrivateReviewResult(BaseModel):
    entity: ResolvedEntity
    signal: Signal
    metrics: list[MetricSeries]
    camels: CamelsScore
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    call_report: dict[str, Any] = Field(default_factory=dict)
    trade_signals: TradeSignal | None = None
    litigation: list[LitigationRecord] = Field(default_factory=list)
    commentary: str = ""


class ResolveEntityInput(BaseModel):
    query: str
    hint_type: EntityType | Literal["auto"] = "auto"


class RunReviewInput(BaseModel):
    entity_id: str
    entity_type: EntityType
    name: str | None = None
    ticker: str | None = None
    cik: str | None = None
    cert_number: str | None = None


class ParseExcelInput(BaseModel):
    file_path: str | None = None
    content_base64: str | None = None


class CommentaryChunk(BaseModel):
    chunk: str
    done: bool = False
