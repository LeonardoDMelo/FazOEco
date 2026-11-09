"""Password hashing, JWT helpers, security headers and rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Callable, Deque
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password for storage."""
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | UUID,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline HTTP security headers to every response."""

    def __init__(self, app: ASGIApp, *, csp: str | None = None) -> None:
        super().__init__(app)
        self.csp = csp or (
            "default-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'; "
            "form-action 'self'"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        response.headers.setdefault("Content-Security-Policy", self.csp)
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        # API responses should not be cached by shared proxies by default.
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response


# ---------------------------------------------------------------------------
# Rate limiting (in-memory sliding window — suitable for single-instance VPS)
# ---------------------------------------------------------------------------


class InMemoryRateLimiter:
    """Thread-safe sliding-window counter keyed by scope + client identity."""

    def __init__(self) -> None:
        self._events: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Record a hit.

        Returns (allowed, retry_after_seconds).
        """
        now = time.monotonic()
        window_start = now - window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])) + 1)
                return False, retry_after
            bucket.append(now)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    return _rate_limiter


def client_identity(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def parse_rate_rule(rule: str) -> tuple[int, int]:
    """Parse ``10/minute`` or ``120/hour`` style rules into (limit, seconds)."""
    raw = (rule or "60/minute").strip().lower()
    try:
        count_str, period = raw.split("/", 1)
        limit = max(1, int(count_str))
    except ValueError:
        return 60, 60
    period = period.strip()
    if period in {"s", "sec", "second", "seconds"}:
        return limit, 1
    if period in {"m", "min", "minute", "minutes"}:
        return limit, 60
    if period in {"h", "hour", "hours"}:
        return limit, 3600
    return limit, 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Apply rate limits to login and public search endpoints.

    - POST /api/v1/auth/login
    - GET  /api/v1/offers (public search / listing)
    """

    LOGIN_PATH = "/api/v1/auth/login"
    SEARCH_PATH = "/api/v1/offers"

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path.rstrip("/") or "/"
        scope: str | None = None
        rule: str | None = None

        if request.method.upper() == "POST" and path == self.LOGIN_PATH.rstrip("/"):
            scope = "login"
            rule = settings.rate_limit_login
        elif request.method.upper() == "GET" and path == self.SEARCH_PATH.rstrip("/"):
            scope = "search"
            rule = settings.rate_limit_search

        if scope and rule:
            limit, window = parse_rate_rule(rule)
            identity = client_identity(request)
            allowed, retry_after = get_rate_limiter().hit(
                f"{scope}:{identity}",
                limit=limit,
                window_seconds=window,
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "scope": scope,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

        return await call_next(request)
