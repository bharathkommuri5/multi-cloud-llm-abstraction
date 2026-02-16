import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class CorrelationIdMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid.uuid4())

        # Attach to request state
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        # Add header in response
        response.headers["X-Correlation-ID"] = correlation_id

        return response
