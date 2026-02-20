"""PayzCore SDK type definitions."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


# ── Chains, Tokens & Statuses ──

Chain = Literal["TRC20", "BEP20", "ERC20", "POLYGON", "ARBITRUM"]

Token = Literal["USDT", "USDC"]

PaymentStatus = Literal[
    "pending",
    "confirming",
    "partial",
    "paid",
    "overpaid",
    "expired",
    "cancelled",
]

WebhookEventType = Literal[
    "payment.completed",
    "payment.overpaid",
    "payment.partial",
    "payment.expired",
    "payment.cancelled",
]


# ── Payments ──


class CreatePaymentParams(TypedDict, total=False):
    amount: float  # required
    chain: Chain  # required
    external_ref: str  # required
    token: Token
    external_order_id: str
    expires_in: int
    metadata: Dict[str, Any]


class Payment(TypedDict, total=False):
    id: str
    address: str
    amount: str
    chain: Chain
    token: Token
    status: PaymentStatus
    expires_at: str
    external_order_id: str
    qr_code: str
    notice: str
    original_amount: str
    requires_txid: bool
    confirm_endpoint: str


class CreatePaymentResponse(TypedDict):
    success: bool
    existing: bool
    payment: Payment


class PaymentListItem(TypedDict, total=False):
    id: str
    external_ref: str
    external_order_id: str
    chain: Chain
    token: Token
    address: str
    expected_amount: str
    paid_amount: str
    status: PaymentStatus
    tx_hash: Optional[str]
    expires_at: str
    paid_at: Optional[str]
    created_at: str


class ListPaymentsParams(TypedDict, total=False):
    status: PaymentStatus
    limit: int
    offset: int


class ListPaymentsResponse(TypedDict):
    success: bool
    payments: List[PaymentListItem]


class Transaction(TypedDict):
    tx_hash: str
    amount: str
    from_address: str
    confirmed: bool
    confirmations: int


class CancelPaymentResponse(TypedDict):
    success: bool
    payment: Dict[str, Any]


class ConfirmPaymentResponse(TypedDict):
    success: bool
    status: PaymentStatus
    verified: bool
    amount_received: Optional[str]
    amount_expected: Optional[str]
    message: Optional[str]


class PaymentDetail(TypedDict, total=False):
    id: str
    status: PaymentStatus
    expected_amount: str
    paid_amount: str
    address: str
    chain: Chain
    token: Token
    tx_hash: Optional[str]
    expires_at: str
    transactions: List[Transaction]


class GetPaymentResponse(TypedDict):
    success: bool
    payment: PaymentDetail


# ── Projects ──


class CreateProjectParams(TypedDict, total=False):
    name: str  # required
    slug: str  # required
    webhook_url: str
    metadata: Dict[str, Any]


class Project(TypedDict, total=False):
    id: str
    name: str
    slug: str
    api_key: str
    webhook_secret: str
    webhook_url: Optional[str]
    created_at: str


class CreateProjectResponse(TypedDict):
    success: bool
    project: Project


class ProjectListItem(TypedDict, total=False):
    id: str
    name: str
    slug: str
    api_key: str
    webhook_url: Optional[str]
    is_active: bool
    created_at: str


class ListProjectsResponse(TypedDict):
    success: bool
    projects: List[ProjectListItem]


# ── Webhooks ──


class WebhookPayload(TypedDict, total=False):
    event: WebhookEventType
    payment_id: str
    external_ref: str
    external_order_id: str
    chain: Chain
    token: Token
    address: str
    expected_amount: str
    paid_amount: str
    tx_hash: Optional[str]
    status: PaymentStatus
    paid_at: Optional[str]
    metadata: Dict[str, Any]
    timestamp: str
