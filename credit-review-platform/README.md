# Credit Review Platform

A full-stack credit review platform combining a **Python 3.12 MCP server** for financial data extraction with a **React + FastAPI** web application. Supports two entity types:

- **Public** — rated/listed companies (SEC EDGAR, NewsAPI)
- **Private** — unrated institutions (FDIC BankFind, FFIEC CDR, NCUA, CourtListener)

## Architecture

```
credit-review-platform/
├── mcp_server/          # MCP stdio server + tools + workflows
├── api/                 # FastAPI REST + WebSocket
├── frontend/            # React 18 + TypeScript + Vite + Tailwind
└── tests/
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+

**You need two terminals** — the frontend proxies API calls to the backend on port 8000. If only Vite is running, you will see `ECONNREFUSED` on `/entities/resolve`.

### Terminal 1 — Backend

```bash
cd credit-review-platform    # project root, NOT frontend/
cp .env.example .env
pip install -e ".[dev]"
python3.12 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Or: `bash scripts/dev-api.sh`

Verify: http://localhost:8000/health → `{"status":"ok",...}`

### Terminal 2 — Frontend

```bash
cd credit-review-platform/frontend
npm install
npm run dev
```

Or: `bash scripts/dev-frontend.sh`

Open http://localhost:5173 — Vite proxies `/api/*` → `http://localhost:8000/*`

> If your prompt already shows `frontend $`, you are inside `frontend/` — do not run `cd frontend` again.

### MCP Server (standalone, optional)

```bash
cd credit-review-platform
python -m mcp_server.server
```

### Tests

```bash
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/entities/resolve` | Resolve entity by name/ticker/cert |
| POST | `/review/run` | Start credit review |
| GET | `/review/{id}` | Get review status/result |
| POST | `/batch/upload` | Upload Excel batch |
| GET | `/batch/{id}` | Batch status |
| WS | `/ws/mcp` | MCP proxy + streaming commentary |
| GET | `/health` | Health check |

## MCP Tools

- `resolve_entity` — Entity resolution (rapidfuzz + FDIC/SEC/NCUA)
- `parse_excel_entities` — Excel batch parsing
- `run_public_review` — Full public entity workflow
- `run_private_review` — Full private entity workflow

## Environment Variables

See `.env.example` for optional API keys (NewsAPI, CourtListener). The platform works without keys using public endpoints and deterministic fallbacks.

## License

MIT
