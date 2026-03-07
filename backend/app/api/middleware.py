"""
EcoScan Middleware
Request/response logging and global error handling.
"""

import time
import logging
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("ecoscan.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming request and outgoing response with timing.
    Catches unhandled exceptions and returns a clean JSON error.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        path = request.url.path

        # Skip noisy health checks from logging
        is_health = "/health" in path

        if not is_health:
            logger.info(f"→ {method} {path}")

        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            if not is_health:
                logger.info(
                    f"← {method} {path} [{response.status_code}] {duration_ms}ms"
                )

            # Add timing header for debugging
            response.headers["X-Process-Time-Ms"] = str(duration_ms)
            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"✖ {method} {path} [{500}] {duration_ms}ms — {str(e)}\n"
                f"{traceback.format_exc()}"
            )
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "An unexpected internal error occurred.",
                    "detail": str(e),
                },
            )
