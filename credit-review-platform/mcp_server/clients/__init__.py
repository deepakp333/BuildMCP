"""External API clients."""

from mcp_server.clients.court_listener import CourtListenerClient
from mcp_server.clients.fdic import FDICClient
from mcp_server.clients.ffiec import FFIECClient
from mcp_server.clients.ncua import NCUAClient
from mcp_server.clients.newsapi import NewsAPIClient
from mcp_server.clients.sec_edgar import SECEdgarClient

__all__ = [
    "FDICClient",
    "FFIECClient",
    "NCUAClient",
    "SECEdgarClient",
    "NewsAPIClient",
    "CourtListenerClient",
]
