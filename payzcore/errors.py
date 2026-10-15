"""PayzCore SDK error classes."""

from __future__ import annotations

from typing import Any, List, Optional


class PayzCoreError(Exception):
    """Base error for all PayzCore API errors."""

    def __init__(
        self,
        message: str,
        status: int,
        code: str,
        details: Optional[List[dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status={self.status}, code={self.code!r})"


class AuthenticationError(PayzCoreError):
    """Raised when the API key is invalid or missing (HTTP 401)."""

    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(message, 401, "authentication_error")


class ForbiddenError(PayzCoreError):
    """Raised when access is denied (HTTP 403)."""

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message, 403, "forbidden")


class NotFoundError(PayzCoreError):
    """Raised when the requested resource is not found (HTTP 404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, 404, "not_found")


class ValidationError(PayzCoreError):
    """Raised when request parameters are invalid (HTTP 400)."""

    def __init__(
        self,
        message: str,
        details: Optional[List[dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message, 400, "validation_error", details)


class RateLimitError(PayzCoreError):
    """Raised when rate limit is exceeded (HTTP 429).

    ``retry_after`` is the absolute Unix timestamp (seconds) from the
    ``X-RateLimit-Reset`` header, not a number of seconds to wait. Use
    ``max(0, err.retry_after - time.time())`` to get the wait time.
    ``is_daily`` is True when the daily plan limit was hit.
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        is_daily: bool = False,
    ) -> None:
        super().__init__(message, 429, "rate_limit_error")
        self.retry_after = retry_after
        self.is_daily = is_daily


class IdempotencyError(PayzCoreError):
    """Raised on any HTTP 409 Conflict.

    Examples: ``external_order_id`` reused with a different ``external_ref`` or
    amount, cancelling a payment that is no longer pending, or submitting a
    tx hash that is already used. Read ``message`` for the exact reason.
    """

    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, 409, "idempotency_error")


class WebhookSignatureError(Exception):
    """Raised when webhook signature verification fails."""

    def __init__(self, message: str = "Webhook signature verification failed") -> None:
        super().__init__(message)
        self.message = message
