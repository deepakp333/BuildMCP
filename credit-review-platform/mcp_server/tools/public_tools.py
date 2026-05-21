"""MCP tools for public/rated entities."""

from __future__ import annotations

from mcp_server.models import PublicReviewResult, ResolvedEntity
from mcp_server.workflows.public_workflow import run_public_review


async def run_public_review_tool(entity: ResolvedEntity) -> PublicReviewResult:
    """Run full public entity credit review."""
    return await run_public_review(entity)
