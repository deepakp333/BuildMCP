"""Shared MCP tools: entity resolution, Excel parsing."""

from __future__ import annotations

import base64
import io
import uuid
from typing import Literal

import pandas as pd
from rapidfuzz import fuzz, process

from mcp_server.clients.fdic import FDICClient
from mcp_server.clients.ncua import NCUAClient
from mcp_server.clients.sec_edgar import SECEdgarClient
from mcp_server.models import EntityType, ExcelEntityRow, ResolvedEntity


async def resolve_entity(
    query: str,
    hint_type: EntityType | Literal["auto"] = "auto",
) -> ResolvedEntity | None:
    """Resolve entity name/ticker/cert to a canonical record."""
    query = query.strip()
    if not query:
        return None

    import httpx

    async with httpx.AsyncClient(timeout=30.0) as http:
        # Try numeric cert first for private
        if query.isdigit() and hint_type in ("auto", EntityType.PRIVATE):
            fdic = FDICClient(http)
            inst = await fdic.get_institution_by_cert(int(query))
            if inst:
                return ResolvedEntity(
                    id=f"fdic-{query}",
                    name=str(inst.get("NAME", "Unknown Institution")),
                    entity_type=EntityType.PRIVATE,
                    cert_number=query,
                    match_score=100.0,
                )

        if hint_type in ("auto", EntityType.PUBLIC) or _looks_like_ticker(query):
            sec = SECEdgarClient(http)
            companies = await sec.search_companies(query)
            if companies:
                best = companies[0]
                score = 95.0 if query.upper() == best.get("ticker", "").upper() else 85.0
                return ResolvedEntity(
                    id=f"sec-{best.get('cik', uuid.uuid4().hex[:8])}",
                    name=best.get("name", query),
                    entity_type=EntityType.PUBLIC,
                    ticker=best.get("ticker"),
                    cik=best.get("cik"),
                    match_score=score,
                )

        if hint_type in ("auto", EntityType.PRIVATE):
            fdic = FDICClient(http)
            institutions = await fdic.search_institutions(query, limit=5)
            if institutions:
                names = [str(i.get("NAME", "")) for i in institutions]
                match = process.extractOne(query, names, scorer=fuzz.WRatio)
                if match and match[1] >= 60:
                    idx = names.index(match[0])
                    inst = institutions[idx]
                    return ResolvedEntity(
                        id=f"fdic-{inst.get('CERT', uuid.uuid4().hex[:8])}",
                        name=match[0],
                        entity_type=EntityType.PRIVATE,
                        cert_number=str(inst.get("CERT", "")),
                        match_score=float(match[1]),
                    )

            ncua = NCUAClient(http)
            cu_results = await ncua.search_credit_union(query, limit=3)
            if cu_results:
                best_cu = cu_results[0]
                return ResolvedEntity(
                    id=f"ncua-{best_cu.get('charter', uuid.uuid4().hex[:8])}",
                    name=str(best_cu.get("name", query)),
                    entity_type=EntityType.PRIVATE,
                    charter_number=str(best_cu.get("charter", "")),
                    match_score=float(best_cu.get("match_score", 80)),
                )

    return ResolvedEntity(
        id=f"unresolved-{uuid.uuid4().hex[:8]}",
        name=query,
        entity_type=EntityType.PUBLIC if hint_type == EntityType.PUBLIC else EntityType.PRIVATE,
        match_score=50.0,
    )


def _looks_like_ticker(q: str) -> bool:
    return len(q) <= 5 and q.isalpha() and q.isupper()


async def parse_excel_entities(
    file_path: str | None = None,
    content_base64: str | None = None,
) -> list[ExcelEntityRow]:
    """Parse Excel file into entity rows."""
    if content_base64:
        raw = base64.b64decode(content_base64)
        df = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    elif file_path:
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        return []

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    rows: list[ExcelEntityRow] = []

    for _, row in df.iterrows():
        name = _cell(row, ["name", "entity_name", "company", "institution"])
        if not name:
            continue
        etype_raw = _cell(row, ["entity_type", "type", "category"], default="private")
        etype = EntityType.PUBLIC if str(etype_raw).lower().startswith("pub") else EntityType.PRIVATE
        rows.append(
            ExcelEntityRow(
                name=str(name),
                entity_type=etype,
                ticker=_cell(row, ["ticker", "symbol"]),
                cert_number=_cell(row, ["cert", "cert_number", "certificate"]),
                notes=_cell(row, ["notes", "comment"]),
            )
        )
    return rows


def _cell(row: pd.Series, keys: list[str], default: str | None = None) -> str | None:
    for k in keys:
        if k in row.index and pd.notna(row[k]):
            return str(row[k]).strip()
    return default
