"""
Request ID Middleware

Generates and propagates X-Request-ID headers for request tracing.
"""

import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable to store request ID for the current request
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_ctx.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates or propagates X-Request-ID headers.

    If the incoming request has an X-Request-ID header, it will be used.
    Otherwise, a new UUID will be generated.

    The request ID is stored in a context variable and added to the response headers.
    """

    HEADER_NAME = "X-Request-ID"

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Get existing request ID from header or generate new one
        request_id = request.headers.get(self.HEADER_NAME)

        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in context variable for use in logging
        token = request_id_ctx.set(request_id)

        try:
            # Store request ID in request state for easy access
            request.state.request_id = request_id

            # Process the request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers[self.HEADER_NAME] = request_id

            return response
        finally:
            # Reset context variable
            request_id_ctx.reset(token)
