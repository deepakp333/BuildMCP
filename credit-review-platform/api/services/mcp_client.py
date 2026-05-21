"""MCP client — spawns and communicates with MCP server via stdio."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MCPClient:
    """Lightweight MCP tool caller using direct Python imports as primary path."""

    def __init__(self) -> None:
        self._use_subprocess = False

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Invoke MCP tool — uses in-process calls for reliability."""
        from mcp_server.models import ResolvedEntity
        from mcp_server.tools.private_tools import run_private_review_tool
        from mcp_server.tools.public_tools import run_public_review_tool
        from mcp_server.tools.shared_tools import parse_excel_entities, resolve_entity

        logger.info("mcp_call_tool", tool=name)

        if name == "resolve_entity":
            hint = arguments.get("hint_type", "auto")
            from mcp_server.models import EntityType

            hint_type: Any = hint
            if hint != "auto":
                hint_type = EntityType(hint)
            result = await resolve_entity(arguments["query"], hint_type)
            return result.model_dump() if result else None

        if name == "parse_excel_entities":
            rows = await parse_excel_entities(
                file_path=arguments.get("file_path"),
                content_base64=arguments.get("content_base64"),
            )
            return [r.model_dump() for r in rows]

        if name == "run_public_review":
            entity = ResolvedEntity.model_validate(arguments["entity"])
            review = await run_public_review_tool(entity)
            return json.loads(review.model_dump_json())

        if name == "run_private_review":
            entity = ResolvedEntity.model_validate(arguments["entity"])
            review = await run_private_review_tool(entity)
            return json.loads(review.model_dump_json())

        raise ValueError(f"Unknown tool: {name}")

    async def call_tool_subprocess(self, name: str, arguments: dict[str, Any]) -> Any:
        """Optional subprocess-based MCP invocation via JSON-RPC over stdio."""
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "mcp_server.server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        if proc.stdin and proc.stdout:
            proc.stdin.write((json.dumps(request) + "\n").encode())
            await proc.stdin.drain()
            line = await proc.stdout.readline()
            proc.terminate()
            if line:
                resp = json.loads(line)
                content = resp.get("result", {}).get("content", [])
                if content:
                    return json.loads(content[0].get("text", "{}"))
        return None


_mcp_client: MCPClient | None = None


def get_mcp_client() -> MCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
