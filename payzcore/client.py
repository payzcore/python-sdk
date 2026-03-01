"""PayzCore HTTP client with retry logic."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from .errors import (
    AuthenticationError,
    ForbiddenError,
    IdempotencyError,
    NotFoundError,
    PayzCoreError,
    RateLimitError,
    ValidationError,
)

DEFAULT_BASE_URL = "https://api.payzcore.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
RETRY_BASE_S = 0.2


class HttpClient:
    """Low-level HTTP client for PayzCore API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        master_key: bool = False,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._use_master_key = master_key
        self._client = httpx.Client(timeout=self._timeout)

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "payzcore-python/1.0.0",
        }
        if self._use_master_key:
            headers["x-master-key"] = self._api_key
        else:
            headers["x-api-key"] = self._api_key
        return headers

    def request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an HTTP request with retry on 5xx errors."""
        url = f"{self._base_url}{path}"
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                time.sleep(RETRY_BASE_S * (2 ** (attempt - 1)))

            try:
                response = self._client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=body,
                )

                if response.is_success:
                    return response.json()

                # Non-retryable errors
                if response.status_code < 500 and response.status_code != 429:
                    _raise_api_error(response)

                # 429 - don't retry
                if response.status_code == 429:
                    _raise_api_error(response)

                # 5xx - retry if attempts remain
                last_error = _build_api_error(response)

            except (
                PayzCoreError,
                AuthenticationError,
                ForbiddenError,
                IdempotencyError,
                NotFoundError,
                ValidationError,
                RateLimitError,
            ):
                raise
            except Exception as exc:
                last_error = exc

        if last_error is not None:
            raise last_error
        raise PayzCoreError("Request failed after retries", 0, "network_error")

    def get(self, path: str) -> Any:
        """Make a GET request."""
        return self.request("GET", path)

    def post(self, path: str, body: Dict[str, Any]) -> Any:
        """Make a POST request."""
        return self.request("POST", path, body)

    def patch(self, path: str, body: Dict[str, Any]) -> Any:
        """Make a PATCH request."""
        return self.request("PATCH", path, body)

    def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.close()
        return False

    def __del__(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass


def _raise_api_error(response: httpx.Response) -> None:
    raise _build_api_error(response)


def _build_api_error(response: httpx.Response) -> PayzCoreError:
    try:
        body = response.json()
    except Exception:
        body = {"error": response.reason_phrase or "Unknown error"}

    message = body.get("error", "Unknown error")

    status = response.status_code
    if status == 400:
        return ValidationError(message, body.get("details"))
    if status == 401:
        return AuthenticationError(message)
    if status == 403:
        return ForbiddenError(message)
    if status == 404:
        return NotFoundError(message)
    if status == 409:
        return IdempotencyError(message)
    if status == 429:
        reset_header = response.headers.get("X-RateLimit-Reset")
        daily_header = response.headers.get("X-RateLimit-Daily")
        retry_after = int(reset_header) if reset_header else None
        is_daily = daily_header == "true"
        return RateLimitError(message, retry_after, is_daily)

    return PayzCoreError(message, status, "api_error")
