"""Tests for private entity credit review workflow."""

from __future__ import annotations

import pytest

from mcp_server.models import EntityType, ResolvedEntity, Signal
from mcp_server.workflows.private_workflow import run_private_review


@pytest.fixture
def bank_entity() -> ResolvedEntity:
    return ResolvedEntity(
        id="fdic-628",
        name="JPMORGAN CHASE BANK, NATIONAL ASSOCIATION",
        entity_type=EntityType.PRIVATE,
        cert_number="628",
        match_score=90.0,
    )


@pytest.fixture
def cu_entity() -> ResolvedEntity:
    return ResolvedEntity(
        id="ncua-68433",
        name="NAVY FEDERAL CREDIT UNION",
        entity_type=EntityType.PRIVATE,
        charter_number="68433",
        match_score=88.0,
    )


@pytest.mark.asyncio
async def test_private_review_with_cert(bank_entity: ResolvedEntity) -> None:
    result = await run_private_review(bank_entity)
    assert result.entity.entity_type == EntityType.PRIVATE
    assert result.signal in list(Signal)
    assert result.camels.composite >= 1.0
    assert len(result.metrics) >= 3
    assert result.commentary


@pytest.mark.asyncio
async def test_private_review_ncua_charter(cu_entity: ResolvedEntity) -> None:
    result = await run_private_review(cu_entity)
    assert result.call_report.get("source") == "NCUA"
    assert result.trade_signals is not None
    assert len(result.litigation) >= 1


@pytest.mark.asyncio
async def test_private_camels_composite_range(bank_entity: ResolvedEntity) -> None:
    result = await run_private_review(bank_entity)
    assert 1.0 <= result.camels.composite <= 5.0
