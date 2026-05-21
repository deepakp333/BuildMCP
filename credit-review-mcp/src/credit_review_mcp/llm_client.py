"""Anthropic Claude client for narrative memo synthesis only."""

from __future__ import annotations

import json
import logging
from typing import Any

from credit_review_mcp.config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MAX_OUTPUT_TOKENS,
    CLAUDE_MODEL,
    USE_LLM_FOR_MEMO,
)

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    return max(1, len(text) // 4)


def llm_available() -> bool:
    return bool(ANTHROPIC_API_KEY) and USE_LLM_FOR_MEMO


def synthesize_memo_narrative(compact_payload: dict[str, Any]) -> tuple[str, dict[str, int] | None]:
    """
    Call Claude for narrative sections only.
    Returns (narrative_text, token_usage dict or None).
    """
    if not llm_available():
        logger.info("LLM memo synthesis skipped (no API key or USE_LLM_FOR_MEMO=false)")
        return "", None

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed")
        return "", None

    payload_str = json.dumps(compact_payload, default=str)
    input_tokens_est = estimate_tokens(payload_str)
    max_input_budget = 12000
    if input_tokens_est > max_input_budget:
        logger.warning("Truncating LLM payload from ~%s to budget", input_tokens_est)
        payload_str = payload_str[: max_input_budget * 4]

    system = (
        "You are assisting a senior credit analyst drafting a DEMO credit memo. "
        "Use only the structured JSON provided. Do not invent sources, ratings, or approvals. "
        "Be concise, factual, and flag data gaps. No investment advice or rating actions."
    )
    user_prompt = (
        "Synthesize narrative paragraphs for a draft credit memo using ONLY this JSON:\n"
        f"{payload_str}\n\n"
        "Return plain text with section headers matching the memo structure. "
        "Keep under 900 words."
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_OUTPUT_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )
        text_parts = [b.text for b in response.content if hasattr(b, "text")]
        narrative = "\n".join(text_parts)
        usage = None
        if response.usage:
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        return narrative, usage
    except Exception as exc:
        logger.error("LLM synthesis failed: %s", exc)
        return "", None
