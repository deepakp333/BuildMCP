"""Application configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"
OUTPUT_DIR = PROJECT_ROOT / "output"
MEMOS_DIR = OUTPUT_DIR / "memos"
RUNS_DIR = OUTPUT_DIR / "runs"

for _dir in (OUTPUT_DIR, MEMOS_DIR, RUNS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# Anthropic / LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_OUTPUT_TOKENS = int(os.getenv("CLAUDE_MAX_OUTPUT_TOKENS", "900"))
USE_LLM_FOR_MEMO = os.getenv("USE_LLM_FOR_MEMO", "false").lower() in ("1", "true", "yes")
USE_LLM_FOR_SENTIMENT = os.getenv("USE_LLM_FOR_SENTIMENT", "false").lower() in (
    "1",
    "true",
    "yes",
)

# SEC
SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "CreditReviewDemo contact@example.com",
)
SEC_BASE_URL = "https://data.sec.gov"
SEC_RATE_LIMIT_PER_SECOND = 8

# Demo limits
MAX_COMPANIES_DEFAULT = int(os.getenv("MAX_COMPANIES_DEFAULT", "5"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))

# News API keys (optional)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "").strip()
REUTERS_API_KEY = os.getenv("REUTERS_API_KEY", "").strip()
BLOOMBERG_API_KEY = os.getenv("BLOOMBERG_API_KEY", "").strip()

DISCLAIMER = (
    "Draft generated for analyst review. Not a rating action, "
    "investment recommendation, or credit approval."
)

TRUSTED_NEWS_SOURCES = (
    "Reuters",
    "Bloomberg",
    "Wall Street Journal",
    "Associated Press",
    "SEC Filings",
    "Company IR",
    "Yahoo Finance",
)
