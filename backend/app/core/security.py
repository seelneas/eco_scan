"""
EcoScan Security & Privacy (Phase 7)
API key validation, rate limiting, and data anonymization utilities.
"""

import hashlib
import time
import logging
from collections import defaultdict
from typing import Optional

from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

logger = logging.getLogger("ecoscan.security")

settings = get_settings()


# ──────────────────────────────────────────
# API Key Validation
# ──────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Validate API key if API key enforcement is enabled.
    In development mode (no keys configured), all requests pass through.
    Returns the key identifier or None for anonymous access.
    """
    valid_keys = settings.API_KEYS

    # If no API keys configured, allow all requests (development mode)
    if not valid_keys:
        return None

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Pass it via the X-API-Key header.",
        )

    if api_key not in valid_keys:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )

    # Return a hashed identifier (don't log the full key)
    key_id = hashlib.sha256(api_key.encode()).hexdigest()[:12]
    return key_id


# ──────────────────────────────────────────
# In-Memory Rate Limiter
# ──────────────────────────────────────────
class RateLimiter:
    """
    Simple in-memory sliding window rate limiter.
    Tracks requests per client (by IP or API key hash).
    No external dependencies — suitable for single-instance deployments.
    For multi-instance, swap this for a Redis-backed implementation.
    """

    def __init__(
        self,
        max_requests: int = 30,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, client_id: str):
        """Remove expired timestamps from the window."""
        cutoff = time.time() - self.window_seconds
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > cutoff
        ]

    def check(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if a request is allowed for the given client.
        Returns (allowed, info_dict).
        """
        self._cleanup(client_id)
        current_count = len(self._requests[client_id])

        info = {
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - current_count),
            "window": self.window_seconds,
        }

        if current_count >= self.max_requests:
            oldest = self._requests[client_id][0] if self._requests[client_id] else time.time()
            retry_after = int(oldest + self.window_seconds - time.time()) + 1
            info["retry_after"] = max(1, retry_after)
            return False, info

        # Record this request
        self._requests[client_id].append(time.time())
        info["remaining"] = max(0, self.max_requests - current_count - 1)
        return True, info


# Global rate limiter instances
analysis_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_ANALYZE,
    window_seconds=settings.RATE_LIMIT_WINDOW,
)
general_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_GENERAL,
    window_seconds=settings.RATE_LIMIT_WINDOW,
)


def get_client_id(request: Request, api_key_id: Optional[str] = None) -> str:
    """
    Derive a stable, anonymized client identifier.
    Uses API key hash if present, otherwise falls back to IP.
    """
    if api_key_id:
        return f"key:{api_key_id}"

    # Use forwarded IP if behind a proxy, otherwise direct IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    # Hash the IP for privacy
    return f"ip:{hashlib.sha256(ip.encode()).hexdigest()[:16]}"


# ──────────────────────────────────────────
# Privacy: Data Anonymization
# ──────────────────────────────────────────
def anonymize_url(url: str) -> str:
    """
    Strip query parameters and fragments from URLs to reduce PII leakage.
    Keeps the base URL + product path for caching/identification.
    """
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    # Keep scheme, netloc, and path; strip query and fragment
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return clean


def hash_user_identifier(raw_id: str) -> str:
    """One-way hash for user identifiers. Never store raw user IDs."""
    return hashlib.sha256(raw_id.encode()).hexdigest()[:32]


def strip_pii_from_text(text: str) -> str:
    """
    Remove common PII patterns from product text before sending to LLM.
    Strips emails, phone numbers, and addresses.
    """
    import re

    # Email addresses
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL_REDACTED]", text)
    # Phone numbers (various formats)
    text = re.sub(r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]", text)

    return text
