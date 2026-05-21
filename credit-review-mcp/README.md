# credit-review-mcp

Demo-grade **Model Context Protocol (MCP)** server for a credit analyst GenAI proof of concept. The server shows how an analyst can scan a small public-company universe, pull SEC and market data, compute deterministic credit ratios, run an adapted **CAMEL** assessment, gather trusted news (or labeled mock news), and produce a **draft credit memo** with PDF export.

> **Disclaimer:** Draft generated for analyst review. Not a rating action, investment recommendation, or credit approval.

## Features

- **11 MCP tools** — universe load, SEC/Yahoo fetch, ratios, news, sentiment, CAMEL, memo, PDF, full demo workflow
- **MCP resources** — input schema, ratio formulas, CAMEL framework, sample CSV
- **MCP prompts** — memo, workflow, analyst challenge
- **Deterministic analytics** — ratios and CAMEL scores (1 = strong, 5 = weak)
- **Optional Claude narrative** — `USE_LLM_FOR_MEMO=true` + `ANTHROPIC_API_KEY`; compact JSON only
- **Streamlit UI** — upload CSV, run pipeline, preview results, download PDF
- **Works offline-ish** — mock news and template memo when APIs/keys unavailable

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) or pip

## Quick start

```bash
cd credit-review-mcp
cp .env.example .env
# Edit SEC_USER_AGENT with your contact email (SEC policy)

uv sync
# or: pip install -e ".[dev]"

pytest
python -m credit_review_mcp.server   # MCP stdio server
streamlit run ui/streamlit_app.py    # Demo UI
```

### Run demo from CLI (Python)

```python
from credit_review_mcp.workflow import run_demo_credit_review

result = run_demo_credit_review("sample_data/companies.csv", max_companies=3)
print(result.summary)
for r in result.results:
    print(r.company.ticker, r.pdf_path)
```

PDFs are written to `output/memos/`; run JSON to `output/runs/`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEC_USER_AGENT` | demo placeholder | **Required** for SEC — include contact email |
| `ANTHROPIC_API_KEY` | — | Optional; enables LLM memo narrative |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Anthropic model |
| `CLAUDE_MAX_OUTPUT_TOKENS` | `900` | Memo token cap |
| `USE_LLM_FOR_MEMO` | `false` | Enable LLM synthesis |
| `USE_LLM_FOR_SENTIMENT` | `false` | LLM sentiment (off by default) |
| `MAX_COMPANIES_DEFAULT` | `5` | Demo cap |
| `NEWS_API_KEY` | — | Optional NewsAPI adapter |

## MCP client usage

Start the server:

```bash
python -m credit_review_mcp.server
```

Example tool sequence:

1. `load_company_universe` — `csv_path`: `sample_data/companies.csv`, `max_companies`: 3
2. `run_demo_credit_review` — same path (runs full pipeline)
3. Or step-wise: `fetch_sec_financials`, `fetch_yahoo_market_data`, `calculate_credit_ratios`, `collect_trusted_news`, `run_camel_assessment`, `generate_credit_memo`, `export_credit_memo_pdf`

Resources:

- `credit://schema/company-input`
- `credit://schema/credit-ratios`
- `credit://framework/camel`
- `credit://demo/sample-companies`

## Project layout

```
credit-review-mcp/
  src/credit_review_mcp/   # Core package
  ui/streamlit_app.py
  sample_data/companies.csv
  tests/
  output/memos/            # Generated PDFs
  output/runs/             # JSON audit trail
```

## Credit ratios (deterministic)

| Ratio | Formula |
|-------|---------|
| Debt / EBITDA | Total Debt ÷ EBITDA |
| Debt / Equity | Total Debt ÷ Equity |
| Interest Coverage | EBITDA ÷ Interest Expense |
| EBITDA Margin | EBITDA ÷ Revenue |
| Current / Quick Ratio | Standard definitions |
| FCF / Debt, Cash / Debt | Cash flow vs leverage |
| Revenue / EBITDA Growth YoY | Period-over-period |
| Liabilities / Assets | Balance sheet leverage |

Altman-style **warning flags** only when inputs exist — not a published Z-score.

## CAMEL (adapted)

| Component | Focus |
|-----------|--------|
| Capital Adequacy | Leverage, equity cushion |
| Asset Quality | Working capital, intangibles |
| Management Capability | News/filing red flags (demo proxies) |
| Earnings | Growth, margins, profitability |
| Liquidity | Current ratio, cash, FCF vs debt |

## Limitations (demo)

- Not a production rating engine
- SEC tag coverage varies by filer; Yahoo fills gaps
- News may be **MOCK** (`is_mock=True`) without API keys
- No paywall scraping; trusted sources via adapters only
- CAMEL scores are rules-based, not regulatory CAMELS
- Analyst must verify all figures against primary filings

## Security & compliance

- Source provenance on every metric
- No hallucinated sources in template mode
- LLM receives only compact summaries
- Stale/missing data flagged in memo

## License

MIT — demo use only.
