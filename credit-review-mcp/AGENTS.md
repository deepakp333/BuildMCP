# AGENTS.md — Credit Review MCP

## Project purpose

Demo-grade MCP server for credit analyst GenAI POC. Deterministic math; LLM only for optional memo narrative.

## Key commands

```bash
cd credit-review-mcp
uv sync   # or: pip install -e ".[dev]"
pytest
python -m credit_review_mcp.server
streamlit run ui/streamlit_app.py
```

## Architecture

- `workflow.py` — orchestration
- `ratios.py` / `camel.py` — deterministic analytics
- `sec_client.py` / `yahoo_client.py` / `news_client.py` — data adapters with provenance
- `memo.py` / `llm_client.py` / `pdf_export.py` — outputs
- `server.py` — FastMCP tools, resources, prompts

## Guardrails

- No rating actions, approvals, or investment advice
- Mock news clearly labeled `is_mock=True`
- Never send full SEC filings to LLM
- All outputs require analyst review

## Environment

Copy `.env.example` to `.env`. Set `SEC_USER_AGENT` with contact email for SEC compliance.
