"""MCP server entry point (stdio transport)."""

from __future__ import annotations

import json

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_server.models import EntityType, ResolvedEntity
from mcp_server.tools.private_tools import run_private_review_tool
from mcp_server.tools.public_tools import run_public_review_tool
from mcp_server.tools.shared_tools import parse_excel_entities, resolve_entity

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ]
)
logger = structlog.get_logger(__name__)

app = Server("credit-review-platform")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="resolve_entity",
            description="Resolve entity by name, ticker, or FDIC certificate number",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "hint_type": {
                        "type": "string",
                        "enum": ["public", "private", "auto"],
                        "default": "auto",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="parse_excel_entities",
            description="Parse uploaded Excel file into entity list",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "content_base64": {"type": "string"},
                },
            },
        ),
        Tool(
            name="run_public_review",
            description="Run full credit review for a public/rated entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity": {"type": "object", "description": "ResolvedEntity dict"},
                },
                "required": ["entity"],
            },
        ),
        Tool(
            name="run_private_review",
            description="Run full credit review for a private entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity": {"type": "object", "description": "ResolvedEntity dict"},
                },
                "required": ["entity"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info("tool_called", name=name)
    try:
        if name == "resolve_entity":
            query = arguments.get("query", "")
            hint = arguments.get("hint_type", "auto")
            hint_type: EntityType | str = hint
            if hint != "auto":
                hint_type = EntityType(hint)
            result = await resolve_entity(query, hint_type)  # type: ignore[arg-type]
            payload = result.model_dump() if result else None
            return [TextContent(type="text", text=json.dumps(payload, default=str))]

        if name == "parse_excel_entities":
            rows = await parse_excel_entities(
                file_path=arguments.get("file_path"),
                content_base64=arguments.get("content_base64"),
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps([r.model_dump() for r in rows], default=str),
                )
            ]

        if name == "run_public_review":
            entity_data = arguments.get("entity", {})
            entity = ResolvedEntity.model_validate(entity_data)
            review = await run_public_review_tool(entity)
            return [TextContent(type="text", text=review.model_dump_json())]

        if name == "run_private_review":
            entity_data = arguments.get("entity", {})
            entity = ResolvedEntity.model_validate(entity_data)
            review = await run_private_review_tool(entity)
            return [TextContent(type="text", text=review.model_dump_json())]

        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    except Exception as exc:
        logger.exception("tool_error", name=name)
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]


async def main() -> None:
    """Run MCP server on stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
