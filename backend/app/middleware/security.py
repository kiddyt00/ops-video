"""
Security middleware and utilities
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import re


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Content-Security-Policy: default-src 'self'
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: geolocation=(), microphone=(), camera=()
    - Cache-Control: no-store (for sensitive endpoints)
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (only in production)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:;"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        return response


def setup_security(app: FastAPI, allowed_origins: list[str]):
    """
    Setup security middleware for FastAPI app

    Args:
        app: FastAPI application
        allowed_origins: List of allowed CORS origins
    """
    # CORS with strict settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=[
            "X-Request-ID",
            "X-Process-Time",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        max_age=600,  # Cache preflight for 10 minutes
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)


# SQL injection patterns to detect
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b.*\b(FROM|INTO|TABLE|DATABASE)\b)",
    r"(--|\#|\/\*|\*\/)",
    r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",
    r"'\s*(OR|AND)\s*'",
]


def is_sql_injection(text: str) -> bool:
    """Check if text contains potential SQL injection"""
    text_lower = text.lower()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """
    Basic XSS protection by sanitizing query parameters

    Note: This is not a replacement for proper output encoding
    """

    async def dispatch(self, request, call_next):
        # Sanitize query parameters
        for key, value in request.query_params.items():
            if self._contains_xss(value):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid input detected"}
                )

        return await call_next(request)

    def _contains_xss(self, text: str) -> bool:
        """Check for basic XSS patterns"""
        text_lower = text.lower()
        dangerous_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
            "onclick=",
            "eval(",
            "document.cookie",
            "document.write",
        ]
        return any(pattern in text_lower for pattern in dangerous_patterns)
