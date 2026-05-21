"""Review execution and storage service."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

from api.services.mcp_client import get_mcp_client
from mcp_server.analysis.commentary import stream_commentary_chunks
from mcp_server.models import EntityType, PrivateReviewResult, PublicReviewResult, ResolvedEntity

logger = structlog.get_logger(__name__)


@dataclass
class ReviewRecord:
    review_id: str
    status: str
    entity_type: EntityType
    entity: ResolvedEntity | None = None
    result: PublicReviewResult | PrivateReviewResult | None = None
    error: str | None = None
    commentary_subscribers: list[asyncio.Queue] = field(default_factory=list)


@dataclass
class BatchRecord:
    batch_id: str
    status: str
    entities: list
    review_ids: list[str] = field(default_factory=list)
    completed: int = 0


class ReviewStore:
    """In-memory review and batch storage."""

    def __init__(self) -> None:
        self.reviews: dict[str, ReviewRecord] = {}
        self.batches: dict[str, BatchRecord] = {}

    def create_review(self, entity_type: EntityType, entity: ResolvedEntity | None) -> str:
        review_id = f"review-{uuid.uuid4().hex[:12]}"
        self.reviews[review_id] = ReviewRecord(
            review_id=review_id,
            status="pending",
            entity_type=entity_type,
            entity=entity,
        )
        return review_id

    def get_review(self, review_id: str) -> ReviewRecord | None:
        return self.reviews.get(review_id)

    def create_batch(self, batch_id: str, entities: list) -> BatchRecord:
        record = BatchRecord(batch_id=batch_id, status="pending", entities=entities)
        self.batches[batch_id] = record
        return record

    def get_batch(self, batch_id: str) -> BatchRecord | None:
        return self.batches.get(batch_id)


_store = ReviewStore()


def get_store() -> ReviewStore:
    return _store


async def run_review(
    review_id: str,
    entity: ResolvedEntity,
    entity_type: EntityType,
    on_commentary_chunk: Any | None = None,
) -> ReviewRecord:
    """Execute review workflow and store result."""
    store = get_store()
    record = store.get_review(review_id)
    if not record:
        raise ValueError(f"Review not found: {review_id}")

    record.status = "running"
    record.entity = entity
    client = get_mcp_client()

    try:
        tool = "run_public_review" if entity_type == EntityType.PUBLIC else "run_private_review"
        raw = await client.call_tool(tool, {"entity": entity.model_dump()})

        if entity_type == EntityType.PUBLIC:
            result = PublicReviewResult.model_validate(raw)
        else:
            result = PrivateReviewResult.model_validate(raw)

        record.result = result
        record.status = "completed"

        if on_commentary_chunk and result.commentary:
            async for chunk in stream_commentary_chunks(result.commentary):
                if chunk:
                    await on_commentary_chunk(review_id, chunk)

    except Exception as exc:
        logger.exception("review_failed", review_id=review_id)
        record.status = "failed"
        record.error = str(exc)

    return record


async def run_batch_reviews(batch_id: str) -> None:
    """Run reviews for all entities in a batch."""
    store = get_store()
    batch = store.get_batch(batch_id)
    if not batch:
        return

    batch.status = "running"
    for entity_row in batch.entities:
        from mcp_server.models import EntityType as ET

        entity_type = entity_row.entity_type if hasattr(entity_row, "entity_type") else ET.PRIVATE
        resolved = await get_mcp_client().call_tool(
            "resolve_entity",
            {"query": entity_row.name, "hint_type": entity_type.value},
        )
        if not resolved:
            continue
        entity = ResolvedEntity.model_validate(resolved)
        review_id = store.create_review(entity_type, entity)
        batch.review_ids.append(review_id)
        await run_review(review_id, entity, entity_type)
        batch.completed += 1

    batch.status = "completed"
