import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("fastapi.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()
        logger.info(f"[{request_id}] → {request.method} {request.url.path}")

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(f"[{request_id}] ← {response.status_code} ({duration_ms:.1f}ms)")

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        return response
