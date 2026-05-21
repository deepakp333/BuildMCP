"""Linear regression trend analysis."""

from __future__ import annotations

import numpy as np
from scipy import stats

from mcp_server.models import CamelsScore, RiskFlag, Signal


def fit_trend(values: list[float]) -> tuple[float, str]:
    """
    Fit linear trend to a series of values.
    Returns (slope, direction) where direction is 'up', 'down', or 'flat'.
    """
    if len(values) < 2:
        return 0.0, "flat"

    x = np.arange(len(values), dtype=float)
    y = np.array(values, dtype=float)
    slope, _intercept, _r, _p, _se = stats.linregress(x, y)

    if abs(slope) < 0.01 * (np.mean(np.abs(y)) + 1e-6):
        direction = "flat"
    elif slope > 0:
        direction = "up"
    else:
        direction = "down"

    return round(float(slope), 6), direction


def compute_signal(
    camels: CamelsScore | None,
    risk_flags: list[RiskFlag],
) -> Signal:
    """Map CAMELS composite and risk flags to overall credit signal."""
    high_flags = [f for f in risk_flags if f.severity == "high"]
    medium_flags = [f for f in risk_flags if f.severity == "medium"]

    if high_flags:
        return Signal.WEAK

    composite = camels.composite if camels else 3.0

    if composite >= 4.0 and len(medium_flags) == 0:
        return Signal.STRONG
    if composite >= 3.5 and len(medium_flags) <= 1:
        return Signal.ADEQUATE
    if composite < 2.5 or len(medium_flags) >= 3:
        return Signal.WEAK
    return Signal.WATCH


def detect_risk_signal(slope: float, metric_key: str, adverse_direction: str = "down") -> bool:
    """Detect if trend slope indicates adverse movement for a metric."""
    if metric_key in ("roa", "roe", "capital_ratio"):
        return slope < -0.05
    if metric_key in ("npl_ratio", "leverage"):
        return slope > 0.05
    if adverse_direction == "down":
        return slope < -0.05
    return slope > 0.05
