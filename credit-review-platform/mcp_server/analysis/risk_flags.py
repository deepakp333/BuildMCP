"""Threshold breach detection for risk flags."""

from __future__ import annotations

from mcp_server.analysis.trends import detect_risk_signal
from mcp_server.models import MetricSeries, RiskFlag


THRESHOLDS = {
    "npl_ratio": {"high": 3.0, "medium": 2.0, "low": 1.0},
    "leverage": {"high": 15.0, "medium": 12.0, "low": 10.0},
    "roa": {"high_low": 0.0, "medium_low": 0.5, "low_low": 0.8},
    "capital_ratio": {"high_low": 6.0, "medium_low": 8.0, "low_low": 10.0},
    "roe": {"high_low": 0.0, "medium_low": 5.0, "low_low": 8.0},
}


def detect_risk_flags(
    ratios: dict[str, float],
    metrics: list[MetricSeries] | None = None,
    litigation_count: int = 0,
    negative_news_count: int = 0,
) -> list[RiskFlag]:
    """Detect risk flags from ratios, trends, and external signals."""
    flags: list[RiskFlag] = []

    npl = ratios.get("npl_ratio", 0)
    if npl >= THRESHOLDS["npl_ratio"]["high"]:
        flags.append(
            RiskFlag(
                code="NPL_HIGH",
                severity="high",
                message=f"NPL ratio {npl:.2f}% exceeds high threshold (3.0%)",
                metric_key="npl_ratio",
            )
        )
    elif npl >= THRESHOLDS["npl_ratio"]["medium"]:
        flags.append(
            RiskFlag(
                code="NPL_ELEVATED",
                severity="medium",
                message=f"NPL ratio {npl:.2f}% above watch level (2.0%)",
                metric_key="npl_ratio",
            )
        )

    leverage = ratios.get("leverage", 0)
    if leverage >= THRESHOLDS["leverage"]["high"]:
        flags.append(
            RiskFlag(
                code="LEVERAGE_HIGH",
                severity="high",
                message=f"Leverage {leverage:.1f}x exceeds policy limit (15x)",
                metric_key="leverage",
            )
        )
    elif leverage >= THRESHOLDS["leverage"]["medium"]:
        flags.append(
            RiskFlag(
                code="LEVERAGE_ELEVATED",
                severity="medium",
                message=f"Leverage {leverage:.1f}x above watch level (12x)",
                metric_key="leverage",
            )
        )

    roa = ratios.get("roa", 0)
    if roa < THRESHOLDS["roa"]["high_low"]:
        flags.append(
            RiskFlag(
                code="ROA_NEGATIVE",
                severity="high",
                message=f"ROA {roa:.2f}% is negative — earnings impairment",
                metric_key="roa",
            )
        )
    elif roa < THRESHOLDS["roa"]["medium_low"]:
        flags.append(
            RiskFlag(
                code="ROA_WEAK",
                severity="medium",
                message=f"ROA {roa:.2f}% below minimum target (0.5%)",
                metric_key="roa",
            )
        )

    capital = ratios.get("capital_ratio", 0)
    if capital < THRESHOLDS["capital_ratio"]["high_low"]:
        flags.append(
            RiskFlag(
                code="CAPITAL_CRITICAL",
                severity="high",
                message=f"Capital ratio {capital:.1f}% below regulatory minimum",
                metric_key="capital_ratio",
            )
        )
    elif capital < THRESHOLDS["capital_ratio"]["medium_low"]:
        flags.append(
            RiskFlag(
                code="CAPITAL_LOW",
                severity="medium",
                message=f"Capital ratio {capital:.1f}% below internal target (8%)",
                metric_key="capital_ratio",
            )
        )

    if metrics:
        for m in metrics:
            if m.trend_slope is not None and detect_risk_signal(m.trend_slope, m.key):
                flags.append(
                    RiskFlag(
                        code=f"TREND_{m.key.upper()}",
                        severity="low",
                        message=f"Adverse trend detected in {m.label} ({m.trend_direction})",
                        metric_key=m.key,
                    )
                )

    if litigation_count >= 3:
        flags.append(
            RiskFlag(
                code="LITIGATION_HIGH",
                severity="high",
                message=f"{litigation_count} active litigation matters identified",
            )
        )
    elif litigation_count >= 1:
        flags.append(
            RiskFlag(
                code="LITIGATION_PRESENT",
                severity="medium",
                message=f"{litigation_count} litigation matter(s) on record",
            )
        )

    if negative_news_count >= 3:
        flags.append(
            RiskFlag(
                code="NEWS_NEGATIVE",
                severity="medium",
                message=f"{negative_news_count} negative news articles in review period",
            )
        )

    return flags
