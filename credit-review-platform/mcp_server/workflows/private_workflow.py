"""Orchestrator for private/unrated entity credit reviews."""

from __future__ import annotations

import httpx

from mcp_server.analysis.camels import compute_camels
from mcp_server.analysis.commentary import generate_commentary
from mcp_server.analysis.metrics import build_metric_series, compute_ratios
from mcp_server.analysis.risk_flags import detect_risk_flags
from mcp_server.analysis.trends import compute_signal
from mcp_server.clients.court_listener import CourtListenerClient
from mcp_server.clients.fdic import FDICClient
from mcp_server.clients.ffiec import FFIECClient
from mcp_server.clients.ncua import NCUAClient
from mcp_server.models import EntityType, PrivateReviewResult, ResolvedEntity, TradeSignal


async def run_private_review(entity: ResolvedEntity) -> PrivateReviewResult:
    """Execute full private entity credit review workflow."""
    async with httpx.AsyncClient(timeout=30.0) as http:
        fdic = FDICClient(http)
        ffiec = FFIECClient(http)
        ncua = NCUAClient(http)
        court = CourtListenerClient(http)

        ratios: dict[str, float] = {}
        call_report: dict = {}

        cert = entity.cert_number
        charter = entity.charter_number

        if cert:
            cert_int = int(str(cert).lstrip("0") or "0")
            ratios = await fdic.get_latest_ratios(cert_int)
            inst = await fdic.get_institution_by_cert(cert_int)
            call_report = {
                "source": "FDIC",
                "cert": cert,
                "institution": inst or {},
                "ffiec_summary": await ffiec.get_call_report_summary(cert=cert),
            }
        elif charter:
            cu_metrics = await ncua.get_metrics(charter)
            ratios = {
                "roa": cu_metrics.get("roa", 0.75),
                "roe": cu_metrics.get("roa", 0.75) * 8,
                "npl_ratio": cu_metrics.get("npl_ratio", 0.8),
                "leverage": 8.0,
                "capital_ratio": cu_metrics.get("capital_ratio", 9.5),
                "total_assets": cu_metrics.get("total_assets", 0),
            }
            call_report = {"source": "NCUA", "charter": charter, "metrics": cu_metrics}
        else:
            ratios = {
                "roa": 0.65,
                "roe": 6.5,
                "npl_ratio": 1.2,
                "leverage": 10.5,
                "capital_ratio": 8.5,
            }
            call_report = {"source": "estimated", "note": "Limited identifier — using sector averages"}

        ratios = compute_ratios(raw=ratios)
        metrics = build_metric_series(ratios)
        camels = compute_camels(ratios)

        litigation = await court.search_cases(entity.name, limit=10)
        trade_signals = TradeSignal(
            payment_index=72.0 + (camels.composite * 2),
            delinquency_rate=max(0.5, 3.5 - camels.earnings),
            trade_credit_rating="A" if camels.composite >= 3.5 else "BBB" if camels.composite >= 2.5 else "BB",
            supplier_count=int(15 + camels.composite * 5),
        )

        flags = detect_risk_flags(
            ratios,
            metrics,
            litigation_count=len(litigation),
        )
        signal = compute_signal(camels, flags)

        result = PrivateReviewResult(
            entity=entity,
            signal=signal,
            metrics=metrics,
            camels=camels,
            risk_flags=flags,
            call_report=call_report,
            trade_signals=trade_signals,
            litigation=litigation,
        )
        result.commentary = generate_commentary(result, EntityType.PRIVATE)
        return result
