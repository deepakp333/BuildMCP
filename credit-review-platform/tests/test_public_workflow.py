"""Tests for public entity credit review workflow."""

from __future__ import annotations

import pytest

from mcp_server.models import EntityType, ResolvedEntity, Signal
from mcp_server.workflows.public_workflow import run_public_review


@pytest.fixture
def jpm_entity() -> ResolvedEntity:
    return ResolvedEntity(
        id="sec-0000019617",
        name="JPMORGAN CHASE & CO",
        entity_type=EntityType.PUBLIC,
        ticker="JPM",
        cik="0000019617",
        match_score=95.0,
    )


@pytest.mark.asyncio
async def test_public_review_completes(jpm_entity: ResolvedEntity) -> None:
    result = await run_public_review(jpm_entity)
    assert result.entity.name == jpm_entity.name
    assert result.signal in list(Signal)
    assert len(result.metrics) >= 3
    assert result.commentary
    assert "CREDIT REVIEW" in result.commentary


@pytest.mark.asyncio
async def test_public_review_has_filings_and_news(jpm_entity: ResolvedEntity) -> None:
    result = await run_public_review(jpm_entity)
    assert len(result.filings) >= 1
    assert len(result.news) >= 1
    assert result.camels is not None
    assert result.camels.composite > 0


@pytest.mark.asyncio
async def test_public_review_camels_in_range(jpm_entity: ResolvedEntity) -> None:
    result = await run_public_review(jpm_entity)
    assert 1.0 <= result.camels.composite <= 5.0
