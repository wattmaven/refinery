from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from refinery.logger import set_correlation_id


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding a correlation ID to the request.
    """

    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from headers (if it exists)
        corr_id = request.headers.get("X-Correlation-Id", "")

        # Set the correlation ID in the context
        set_correlation_id(corr_id)

        # Process the request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-Id"] = corr_id

        return response
