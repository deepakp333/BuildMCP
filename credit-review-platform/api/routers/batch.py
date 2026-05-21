"""Batch Excel upload endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from api.models import BatchStatusResponse, BatchUploadResponse
from api.services.excel_service import create_batch_id, parse_uploaded_excel
from api.services.review_service import get_store, run_batch_reviews
from mcp_server.models import ExcelEntityRow

router = APIRouter()


@router.post("/upload", response_model=BatchUploadResponse)
async def upload_batch(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> BatchUploadResponse:
    """Upload Excel batch file and parse entities."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Excel file (.xlsx) required")

    content = await file.read()
    entities = await parse_uploaded_excel(content=content)
    batch_id = create_batch_id()
    store = get_store()
    store.create_batch(batch_id, entities)

    background_tasks.add_task(run_batch_reviews, batch_id)

    return BatchUploadResponse(
        batch_id=batch_id,
        entities=entities,
        count=len(entities),
    )


@router.get("/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str) -> BatchStatusResponse:
    """Get batch processing status."""
    store = get_store()
    batch = store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    return BatchStatusResponse(
        batch_id=batch_id,
        status=batch.status,
        total=len(batch.entities),
        completed=batch.completed,
        review_ids=batch.review_ids,
        entities=[ExcelEntityRow.model_validate(e) if isinstance(e, dict) else e for e in batch.entities],
    )
