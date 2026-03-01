"""PayzCore SDK type definitions."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


# ── Networks, Tokens & Statuses ──

Network = Literal["TRC20", "BEP20", "ERC20", "POLYGON", "ARBITRUM"]

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
    network: Network  # optional — omit to let customer choose on payment page
    external_ref: str  # required
    token: Token
    external_order_id: str
    address: str
    expires_in: int
    metadata: Dict[str, Any]


class AvailableNetwork(TypedDict):
    network: Network
    name: str
    tokens: List[Token]


class Payment(TypedDict, total=False):
    id: str
    address: Optional[str]
    amount: str
    network: Optional[Network]
    token: Optional[Token]
    status: PaymentStatus
    expires_at: str
    external_order_id: str
    qr_code: str
    notice: str
    original_amount: str
    requires_txid: bool
    confirm_endpoint: str
    awaiting_network: bool
    payment_url: str
    available_networks: List[AvailableNetwork]


class CreatePaymentResponse(TypedDict):
    success: bool
    existing: bool
    payment: Payment


class PaymentListItem(TypedDict, total=False):
    id: str
    external_ref: str
    external_order_id: str
    network: Optional[Network]
    token: Optional[Token]
    address: Optional[str]
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
    address: Optional[str]
    network: Optional[Network]
    token: Optional[Token]
    tx_hash: Optional[str]
    expires_at: str
    transactions: List[Transaction]
    awaiting_network: bool


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
    external_order_id: Optional[str]
    network: Network
    token: Token
    address: str
    expected_amount: str
    paid_amount: str
    tx_hash: Optional[str]
    status: PaymentStatus
    paid_at: Optional[str]  # Only set for payment.completed and payment.overpaid; None for others
    metadata: Dict[str, Any]
    timestamp: str
    # Payment link buyer fields (only present for payment link payments)
    buyer_email: Optional[str]
    buyer_name: Optional[str]
    buyer_note: Optional[str]
    payment_link_id: Optional[str]
    payment_link_slug: Optional[str]
