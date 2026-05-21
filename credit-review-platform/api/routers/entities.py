"""Entity resolution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models import ResolveEntityRequest, ResolveEntityResponse
from api.services.mcp_client import get_mcp_client
from mcp_server.models import EntityType, ResolvedEntity

router = APIRouter()


@router.post("/resolve", response_model=ResolveEntityResponse)
async def resolve_entity_endpoint(request: ResolveEntityRequest) -> ResolveEntityResponse:
    """Resolve entity by name, ticker, or certificate."""
    client = get_mcp_client()
    hint = request.entity_type
    hint_type = hint if hint != "auto" else "auto"
    if hint != "auto" and isinstance(hint, EntityType):
        hint_type = hint.value

    result = await client.call_tool(
        "resolve_entity",
        {"query": request.query, "hint_type": hint_type},
    )
    if result is None:
        return ResolveEntityResponse(entity=None)
    entity = ResolvedEntity.model_validate(result)
    return ResolveEntityResponse(entity=entity)
