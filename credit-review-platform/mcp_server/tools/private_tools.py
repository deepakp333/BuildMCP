"""MCP tools for private entities."""

from __future__ import annotations

from mcp_server.models import PrivateReviewResult, ResolvedEntity
from mcp_server.workflows.private_workflow import run_private_review


async def run_private_review_tool(entity: ResolvedEntity) -> PrivateReviewResult:
    """Run full private entity credit review."""
    return await run_private_review(entity)
