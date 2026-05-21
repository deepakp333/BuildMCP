"""FastAPI application entry point."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import batch, entities, mcp_proxy, review

load_dotenv()

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app = FastAPI(
    title="Credit Review Platform",
    description="Credit review for public and private entities with MCP integration",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entities.router, prefix="/entities", tags=["entities"])
app.include_router(review.router, prefix="/review", tags=["review"])
app.include_router(batch.router, prefix="/batch", tags=["batch"])
app.include_router(mcp_proxy.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "credit-review-platform"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api.main:app", host=host, port=port, reload=True)
