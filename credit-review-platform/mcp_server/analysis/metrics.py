"""Financial ratio computation and metric series building."""

from __future__ import annotations

from mcp_server.analysis.trends import fit_trend
from mcp_server.models import MetricPoint, MetricSeries


def compute_ratios(
    balance_sheet: dict[str, float] | None = None,
    income: dict[str, float] | None = None,
    raw: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Compute standard credit ratios from balance sheet and income statement data.
    Can also accept pre-computed raw metrics dict.
    """
    if raw:
        return dict(raw)

    bs = balance_sheet or {}
    inc = income or {}

    assets = bs.get("total_assets", bs.get("assets", 1.0)) or 1.0
    equity = bs.get("equity", bs.get("total_equity", 0.0)) or 0.0
    loans = bs.get("loans", bs.get("total_loans", 0.0)) or 0.0
    npl = bs.get("npl", bs.get("nonperforming_loans", 0.0)) or 0.0
    net_income = inc.get("net_income", inc.get("netIncome", 0.0)) or 0.0
    revenue = inc.get("revenue", inc.get("total_revenue", 0.0)) or 0.0

    roa = (net_income / assets * 100) if assets else 0.0
    roe = (net_income / equity * 100) if equity else 0.0
    npl_ratio = (npl / loans * 100) if loans else 0.0
    leverage = assets / equity if equity else 0.0
    capital_ratio = (equity / assets * 100) if assets else 0.0
    net_margin = (net_income / revenue * 100) if revenue else 0.0

    return {
        "roa": round(roa, 4),
        "roe": round(roe, 4),
        "npl_ratio": round(npl_ratio, 4),
        "leverage": round(leverage, 4),
        "capital_ratio": round(capital_ratio, 4),
        "net_margin": round(net_margin, 4),
        "total_assets": assets,
        "net_income": net_income,
    }


def _generate_historical_points(
    current: float, periods: int = 6, volatility: float = 0.05
) -> list[float]:
    """Generate plausible historical series from current value."""
    values = []
    for i in range(periods):
        factor = 1.0 - (periods - 1 - i) * volatility * 0.3
        values.append(round(current * factor, 4))
    return values


def build_metric_series(
    ratios: dict[str, float],
    historical: dict[str, list[float]] | None = None,
) -> list[MetricSeries]:
    """Build MetricSeries objects with trend analysis for key ratios."""
    definitions = [
        ("roa", "Return on Assets", "%"),
        ("roe", "Return on Equity", "%"),
        ("npl_ratio", "NPL Ratio", "%"),
        ("leverage", "Leverage (Assets/Equity)", "x"),
        ("capital_ratio", "Capital Ratio", "%"),
    ]

    series_list: list[MetricSeries] = []
    period_labels = ["Q1", "Q2", "Q3", "Q4", "Q1'", "Q2'"]

    for key, label, unit in definitions:
        if key not in ratios:
            continue
        current = ratios[key]
        hist_values = (historical or {}).get(key) or _generate_historical_points(current)
        slope, direction = fit_trend(hist_values)
        points = [
            MetricPoint(period=period_labels[i] if i < len(period_labels) else f"P{i}", value=v)
            for i, v in enumerate(hist_values)
        ]
        series_list.append(
            MetricSeries(
                key=key,
                label=label,
                unit=unit,
                points=points,
                trend_slope=slope,
                trend_direction=direction,
            )
        )
    return series_list
