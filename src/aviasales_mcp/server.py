"""Aviasales MCP Server — entry point."""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from aviasales_mcp.config import settings
from aviasales_mcp.tools.flights import (
    get_alternative_directions,
    get_latest_prices,
    get_popular_directions,
    get_prices_calendar,
    search_flights,
)
from aviasales_mcp.tools.reference import (
    lookup_airlines,
    lookup_airports,
    lookup_cities,
    lookup_countries,
)

logging.basicConfig(level=settings.log_level.upper(), format="%(levelname)s %(name)s: %(message)s")

mcp = FastMCP(
    "Aviasales",
    instructions=(
        "Flight search assistant powered by Aviasales/Travelpayouts API. "
        "Use the tools to search flight prices, find cheapest dates, "
        "discover popular directions, and look up airline/airport codes. "
        "All price data comes from the cache of recent user searches (last 48h)."
    ),
)

# Flight tools
mcp.tool()(search_flights)
mcp.tool()(get_prices_calendar)
mcp.tool()(get_latest_prices)
mcp.tool()(get_popular_directions)
mcp.tool()(get_alternative_directions)

# Reference tools
mcp.tool()(lookup_airlines)
mcp.tool()(lookup_airports)
mcp.tool()(lookup_cities)
mcp.tool()(lookup_countries)


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """Require ?token=<TOKEN> query param when TOKEN env var is set."""

    def __init__(self, app: Any, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.query_params.get("token") != self._token:
            return Response("Unauthorized", status_code=401)
        return await call_next(request)


def main() -> None:
    port = os.environ.get("PORT")
    token = os.environ.get("TOKEN")

    if port:
        middleware = [Middleware(TokenAuthMiddleware, token=token)] if token else None
        mcp.run(
            transport="streamable-http",
            port=int(port),
            middleware=middleware,
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
