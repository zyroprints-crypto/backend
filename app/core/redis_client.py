"""Shared Redis connection (sync client) used for OTP storage, caching, rate limiting."""
import redis

from app.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
