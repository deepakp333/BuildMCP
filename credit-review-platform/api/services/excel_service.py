"""Excel upload parsing service."""

from __future__ import annotations

import base64
import uuid

from mcp_server.models import ExcelEntityRow
from mcp_server.tools.shared_tools import parse_excel_entities


async def parse_uploaded_excel(
    content: bytes | None = None,
    content_base64: str | None = None,
) -> list[ExcelEntityRow]:
    """Parse Excel file bytes into entity rows."""
    if content and not content_base64:
        content_base64 = base64.b64encode(content).decode("utf-8")
    return await parse_excel_entities(content_base64=content_base64)


def create_batch_id() -> str:
    return f"batch-{uuid.uuid4().hex[:12]}"
