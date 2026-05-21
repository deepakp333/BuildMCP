"""Credit review endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.models import ReviewStatusResponse, RunReviewRequest, RunReviewResponse
from api.services.review_service import get_store, run_review
from mcp_server.models import EntityType, ResolvedEntity

router = APIRouter()


@router.post("/run", response_model=RunReviewResponse)
async def run_review_endpoint(
    request: RunReviewRequest,
    background_tasks: BackgroundTasks,
) -> RunReviewResponse:
    """Start a credit review for an entity."""
    entity = request.entity
    if not entity and request.entity_id:
        raise HTTPException(status_code=400, detail="entity object required with review request")

    if not entity:
        raise HTTPException(status_code=400, detail="entity is required")

    store = get_store()
    review_id = store.create_review(request.entity_type, entity)

    async def _execute() -> None:
        await run_review(review_id, entity, request.entity_type)

    background_tasks.add_task(_execute)
    return RunReviewResponse(review_id=review_id, status="running")


@router.get("/{review_id}", response_model=ReviewStatusResponse)
async def get_review_endpoint(review_id: str) -> ReviewStatusResponse:
    """Get review status and results."""
    store = get_store()
    record = store.get_review(review_id)
    if not record:
        raise HTTPException(status_code=404, detail="Review not found")

    return ReviewStatusResponse(
        review_id=review_id,
        status=record.status,
        entity_type=record.entity_type,
        result=record.result,
        error=record.error,
    )


@router.post("/{review_id}/stream")
async def stream_review_commentary(review_id: str) -> dict:
    """Trigger commentary streaming for a completed review."""
    store = get_store()
    record = store.get_review(review_id)
    if not record or not record.result:
        raise HTTPException(status_code=404, detail="Review not found or not complete")

    chunks: list[str] = []
    from mcp_server.analysis.commentary import stream_commentary_chunks

    async for chunk in stream_commentary_chunks(record.result.commentary):
        if chunk:
            chunks.append(chunk)

    return {"review_id": review_id, "commentary": "".join(chunks)}
