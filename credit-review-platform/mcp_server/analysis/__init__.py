"""Credit analysis modules."""

from mcp_server.analysis.camels import compute_camels
from mcp_server.analysis.commentary import generate_commentary, stream_commentary_chunks
from mcp_server.analysis.metrics import build_metric_series, compute_ratios
from mcp_server.analysis.risk_flags import detect_risk_flags
from mcp_server.analysis.trends import compute_signal, detect_risk_signal, fit_trend

__all__ = [
    "compute_ratios",
    "build_metric_series",
    "fit_trend",
    "compute_camels",
    "detect_risk_flags",
    "generate_commentary",
    "stream_commentary_chunks",
    "compute_signal",
    "detect_risk_signal",
]
