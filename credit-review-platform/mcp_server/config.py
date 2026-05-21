"""Configuration for MCP server and clients."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    news_api_key: str = ""
    courtlistener_api_token: str = ""
    sec_user_agent: str = "CreditReviewPlatform contact@example.com"
    log_level: str = "INFO"

    fdic_api_base: str = "https://banks.data.fdic.gov/api"
    ffiec_cdr_base: str = "https://cdr.ffiec.gov/public"
    sec_search_base: str = "https://efts.sec.gov/LATEST/search-index"
    sec_submissions_base: str = "https://data.sec.gov/submissions"
    ncua_data_url: str = (
        "https://ncua.gov/analysis/credit-union-corporate-call-report-data"
    )
    news_api_base: str = "https://newsapi.org/v2"
    courtlistener_base: str = "https://www.courtlistener.com/api/rest/v4"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings(
        news_api_key=os.getenv("NEWS_API_KEY", ""),
        courtlistener_api_token=os.getenv("COURTLISTENER_API_TOKEN", ""),
        sec_user_agent=os.getenv("SEC_USER_AGENT", "CreditReviewPlatform contact@example.com"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
