"""Tests for Excel parsing service."""

from __future__ import annotations

import base64
import io

import pandas as pd
import pytest

from api.services.excel_service import parse_uploaded_excel
from mcp_server.tools.shared_tools import parse_excel_entities


@pytest.fixture
def sample_xlsx_bytes() -> bytes:
    df = pd.DataFrame(
        [
            {"name": "JPMorgan Chase", "entity_type": "public", "ticker": "JPM"},
            {"name": "Navy Federal Credit Union", "entity_type": "private", "cert": ""},
            {"name": "Wells Fargo", "entity_type": "public", "ticker": "WFC"},
        ]
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_parse_excel_entities(sample_xlsx_bytes: bytes) -> None:
    b64 = base64.b64encode(sample_xlsx_bytes).decode()
    rows = await parse_excel_entities(content_base64=b64)
    assert len(rows) == 3
    assert rows[0].name == "JPMorgan Chase"
    assert rows[0].entity_type.value == "public"
    assert rows[1].entity_type.value == "private"


@pytest.mark.asyncio
async def test_excel_service_parse(sample_xlsx_bytes: bytes) -> None:
    rows = await parse_uploaded_excel(content=sample_xlsx_bytes)
    assert len(rows) == 3
    assert rows[2].ticker == "WFC"
