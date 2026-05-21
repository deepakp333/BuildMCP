"""Shared utilities: caching, rate limiting, logging, identifiers."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

from credit_review_mcp.config import CACHE_TTL_SECONDS

logger = logging.getLogger("credit_review_mcp")

T = TypeVar("T")

_cache: dict[str, tuple[float, Any]] = {}
_rate_buckets: dict[str, list[float]] = {}


def setup_logging(level: int = logging.INFO) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )


def cache_key(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def get_cached(key: str) -> Any | None:
    entry = _cache.get(key)
    if not entry:
        return None
    ts, value = entry
    if time.time() - ts > CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return value


def set_cached(key: str, value: Any) -> None:
    _cache[key] = (time.time(), value)


def rate_limit(namespace: str, max_per_second: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            now = time.time()
            bucket = _rate_buckets.setdefault(namespace, [])
            bucket[:] = [t for t in bucket if now - t < 1.0]
            min_interval = 1.0 / max_per_second
            if bucket and (now - bucket[-1]) < min_interval:
                time.sleep(min_interval - (now - bucket[-1]))
            bucket.append(time.time())
            return func(*args, **kwargs)

        return wrapper

    return decorator


def normalize_cik(cik: str | int | None) -> str | None:
    if cik is None:
        return None
    digits = re.sub(r"\D", "", str(cik))
    if not digits:
        return None
    return digits.zfill(10)


def safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def save_json(path: Path, data: dict[str, Any] | list[Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S") + "_" + hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
