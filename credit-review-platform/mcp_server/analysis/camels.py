"""CAMELS proxy scoring."""

from __future__ import annotations

from mcp_server.models import CamelsScore


def _score_metric(value: float, good_threshold: float, warn_threshold: float, higher_is_better: bool) -> float:
    """Score a single metric on 1-5 scale."""
    if higher_is_better:
        if value >= good_threshold:
            return 5.0
        if value >= warn_threshold:
            return 3.5
        if value >= warn_threshold * 0.7:
            return 2.5
        return 1.5
    else:
        if value <= good_threshold:
            return 5.0
        if value <= warn_threshold:
            return 3.5
        if value <= warn_threshold * 1.5:
            return 2.5
        return 1.5


def compute_camels(ratios: dict[str, float]) -> CamelsScore:
    """
    Compute CAMELS proxy scores from financial ratios.
    Capital, Asset quality, Management, Earnings, Liquidity, Sensitivity.
    """
    roa = ratios.get("roa", 0.0)
    roe = ratios.get("roe", 0.0)
    npl = ratios.get("npl_ratio", 0.0)
    leverage = ratios.get("leverage", 0.0)
    capital = ratios.get("capital_ratio", 0.0)
    liquidity = ratios.get("liquidity_coverage", ratios.get("liquidity", 100.0))

    capital_score = _score_metric(capital, 10.0, 7.0, higher_is_better=True)
    asset_quality = _score_metric(npl, 1.0, 2.0, higher_is_better=False)
    management = 3.5  # proxy without qualitative data
    earnings = (_score_metric(roa, 1.0, 0.5, True) + _score_metric(roe, 12.0, 6.0, True)) / 2
    liquidity_score = _score_metric(liquidity if liquidity < 200 else 100, 100, 80, higher_is_better=True)
    sensitivity = _score_metric(leverage, 8.0, 12.0, higher_is_better=False)

    weights = {
        "capital": 0.2,
        "asset_quality": 0.2,
        "management": 0.1,
        "earnings": 0.2,
        "liquidity": 0.15,
        "sensitivity": 0.15,
    }
    composite = (
        capital_score * weights["capital"]
        + asset_quality * weights["asset_quality"]
        + management * weights["management"]
        + earnings * weights["earnings"]
        + liquidity_score * weights["liquidity"]
        + sensitivity * weights["sensitivity"]
    )

    return CamelsScore(
        capital=round(capital_score, 2),
        asset_quality=round(asset_quality, 2),
        management=round(management, 2),
        earnings=round(earnings, 2),
        liquidity=round(liquidity_score, 2),
        sensitivity=round(sensitivity, 2),
        composite=round(composite, 2),
    )
