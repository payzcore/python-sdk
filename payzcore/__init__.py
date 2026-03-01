"""PayzCore Python SDK - Blockchain transaction monitoring API client."""

from __future__ import annotations

from .client import HttpClient
from .resources.payments import Payments
from .resources.projects import Projects

# Webhook utilities
from .webhook import (
    SUPPORTED_NETWORKS,
    SUPPORTED_TOKENS,
    construct_event,
    parse_webhook,
    verify_signature,
)

# Error classes
from .errors import (
    AuthenticationError,
    ForbiddenError,
    IdempotencyError,
    NotFoundError,
    PayzCoreError,
    RateLimitError,
    ValidationError,
    WebhookSignatureError,
)

# Types
from .types import (
    AvailableNetwork,
    Network,
    CreatePaymentParams,
    CreatePaymentResponse,
    CreateProjectParams,
    CreateProjectResponse,
    GetPaymentResponse,
    ListPaymentsParams,
    ListPaymentsResponse,
    ListProjectsResponse,
    Payment,
    PaymentDetail,
    PaymentListItem,
    PaymentStatus,
    Project,
    ProjectListItem,
    Token,
    Transaction,
    WebhookEventType,
    WebhookPayload,
)

__version__ = "1.0.0"
__all__ = [
    "PayzCore",
    # Webhook
    "verify_signature",
    "construct_event",
    "parse_webhook",
    "SUPPORTED_NETWORKS",
    "SUPPORTED_TOKENS",
    # Errors
    "PayzCoreError",
    "AuthenticationError",
    "ForbiddenError",
    "IdempotencyError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "WebhookSignatureError",
    # Types
    "AvailableNetwork",
    "Network",
    "Token",
    "PaymentStatus",
    "WebhookEventType",
    "CreatePaymentParams",
    "Payment",
    "CreatePaymentResponse",
    "PaymentListItem",
    "ListPaymentsParams",
    "ListPaymentsResponse",
    "Transaction",
    "PaymentDetail",
    "GetPaymentResponse",
    "CreateProjectParams",
    "Project",
    "CreateProjectResponse",
    "ProjectListItem",
    "ListProjectsResponse",
    "WebhookPayload",
]


class PayzCore:
    """PayzCore API client.

    Usage::

        from payzcore import PayzCore

        # Project API (payment monitoring)
        client = PayzCore("pk_live_xxx")
        payment = client.payments.create(
            amount=50,
            external_ref="user-123",
            network="TRC20",  # optional
        )

        # Admin API (project management)
        admin = PayzCore("mk_xxx", master_key=True)
        projects = admin.projects.list()
    """

    payments: Payments
    projects: Projects

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.payzcore.com",
        timeout: float = 30.0,
        max_retries: int = 2,
        master_key: bool = False,
    ) -> None:
        """Initialize PayzCore client.

        Args:
            api_key: Your API key (pk_live_xxx) or master key (mk_xxx).
            base_url: API base URL. Default: https://api.payzcore.com
            timeout: Request timeout in seconds. Default: 30.0
            max_retries: Max retries on 5xx/network errors. Default: 2
            master_key: Use master key auth (x-master-key header). Default: False
        """
        if not api_key:
            raise ValueError(
                "PayzCore API key is required. Pass your pk_live_xxx or mk_xxx key."
            )

        self._http_client = HttpClient(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            master_key=master_key,
        )
        self.payments = Payments(self._http_client)
        self.projects = Projects(self._http_client)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http_client.close()

    def __enter__(self) -> "PayzCore":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
