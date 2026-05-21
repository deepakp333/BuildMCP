"""API request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from mcp_server.models import (
    EntityType,
    ExcelEntityRow,
    PrivateReviewResult,
    PublicReviewResult,
    ResolvedEntity,
    Signal,
)


class ResolveEntityRequest(BaseModel):
    query: str
    entity_type: EntityType | Literal["auto"] = "auto"


class ResolveEntityResponse(BaseModel):
    entity: ResolvedEntity | None


class RunReviewRequest(BaseModel):
    entity_id: str | None = None
    entity_type: EntityType
    entity: ResolvedEntity | None = None


class RunReviewResponse(BaseModel):
    review_id: str
    status: str = "running"


class ReviewStatusResponse(BaseModel):
    review_id: str
    status: str
    entity_type: EntityType | None = None
    result: PublicReviewResult | PrivateReviewResult | None = None
    error: str | None = None


class BatchUploadResponse(BaseModel):
    batch_id: str
    entities: list[ExcelEntityRow]
    count: int


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total: int
    completed: int
    review_ids: list[str] = Field(default_factory=list)
    entities: list[ExcelEntityRow] = Field(default_factory=list)


class MCPCallRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPCallResponse(BaseModel):
    result: Any
    error: str | None = None


class CommentaryMessage(BaseModel):
    type: Literal["commentary", "status", "error", "complete"] = "commentary"
    chunk: str = ""
    review_id: str | None = None
    done: bool = False
