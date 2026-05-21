"""WebSocket MCP proxy for streaming commentary."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.models import CommentaryMessage
from api.services.mcp_client import get_mcp_client
from api.services.review_service import get_store, run_review
from mcp_server.analysis.commentary import stream_commentary_chunks
from mcp_server.models import EntityType, ResolvedEntity

router = APIRouter()


@router.websocket("/mcp")
async def mcp_websocket(websocket: WebSocket) -> None:
    """
    WebSocket proxy for MCP tool calls and streaming commentary.
    Client sends: {"action": "call_tool", "tool": "...", "arguments": {...}}
    Or: {"action": "run_review", "entity": {...}, "entity_type": "public|private"}
    """
    await websocket.accept()
    client = get_mcp_client()

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action", "call_tool")

            if action == "call_tool":
                tool = msg.get("tool", "")
                arguments = msg.get("arguments", {})
                try:
                    result = await client.call_tool(tool, arguments)
                    await websocket.send_json({"type": "result", "result": result})
                except Exception as exc:
                    await websocket.send_json({"type": "error", "error": str(exc)})

            elif action == "run_review":
                entity_data = msg.get("entity", {})
                entity_type_str = msg.get("entity_type", "public")
                entity = ResolvedEntity.model_validate(entity_data)
                entity_type = EntityType(entity_type_str)

                store = get_store()
                review_id = store.create_review(entity_type, entity)

                await websocket.send_json(
                    CommentaryMessage(
                        type="status",
                        review_id=review_id,
                        chunk="Review started",
                    ).model_dump()
                )

                async def on_chunk(rid: str, chunk: str) -> None:
                    await websocket.send_json(
                        CommentaryMessage(
                            type="commentary",
                            review_id=rid,
                            chunk=chunk,
                        ).model_dump()
                    )

                record = await run_review(
                    review_id,
                    entity,
                    entity_type,
                    on_commentary_chunk=on_chunk,
                )

                if record.result and record.result.commentary:
                    async for chunk in stream_commentary_chunks(record.result.commentary):
                        if chunk:
                            await websocket.send_json(
                                CommentaryMessage(
                                    type="commentary",
                                    review_id=review_id,
                                    chunk=chunk,
                                ).model_dump()
                            )

                await websocket.send_json(
                    CommentaryMessage(
                        type="complete",
                        review_id=review_id,
                        done=True,
                        chunk=json.dumps(record.result.model_dump(), default=str)
                        if record.result
                        else "",
                    ).model_dump()
                )

            elif action == "stream_commentary":
                review_id = msg.get("review_id", "")
                store = get_store()
                record = store.get_review(review_id)
                if record and record.result:
                    async for chunk in stream_commentary_chunks(record.result.commentary):
                        if chunk:
                            await websocket.send_json(
                                CommentaryMessage(
                                    type="commentary",
                                    review_id=review_id,
                                    chunk=chunk,
                                ).model_dump()
                            )
                    await websocket.send_json(
                        CommentaryMessage(type="complete", review_id=review_id, done=True).model_dump()
                    )
                else:
                    await websocket.send_json(
                        CommentaryMessage(type="error", chunk="Review not found").model_dump()
                    )

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "error": str(exc)})
        except Exception:
            pass
