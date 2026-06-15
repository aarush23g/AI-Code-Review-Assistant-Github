"""
Request ID middleware.

Generates a unique request ID for each incoming request, stores it
in a context variable for access in logging, and includes it in
the response headers for client-side correlation.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique ID to each request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Use existing header or generate a new UUID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in context variable for structured logging
        token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)
