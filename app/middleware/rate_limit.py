"""
Simple fixed-window rate limiter backed by Redis. Keyed by client IP.
Good enough for a single-region deployment; swap for a token-bucket /
API-gateway based limiter (e.g. Kong, AWS WAF) at higher scale.
"""
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.redis_client import redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time() // 60)
        key = f"ratelimit:{client_ip}:{window}"

        try:
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, 60)
            if current > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={"success": False, "message": "Too many requests, slow down."},
                )
        except Exception:
            # If Redis is unavailable, fail open rather than blocking all traffic.
            pass

        return await call_next(request)
