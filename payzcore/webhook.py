"""PayzCore webhook signature verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, List, Optional

from .errors import WebhookSignatureError
from .types import WebhookPayload

logger = logging.getLogger("payzcore")

#: Supported blockchain networks.
SUPPORTED_NETWORKS: List[str] = ["TRC20", "BEP20", "ERC20", "POLYGON", "ARBITRUM"]

#: Supported stablecoin tokens.
SUPPORTED_TOKENS: List[str] = ["USDT", "USDC"]


def verify_signature(
    body: str,
    signature: str,
    secret: str,
    timestamp: Optional[str] = None,
    tolerance_seconds: int = 300,
) -> bool:
    """Verify a webhook signature from PayzCore.

    Uses HMAC-SHA256 with timing-safe comparison to prevent timing attacks.
    The signature covers ``timestamp + "." + body`` to bind the timestamp
    to the payload and prevent replay attacks with modified timestamps.

    Args:
        body: Raw request body string.
        signature: Value of X-PayzCore-Signature header.
        secret: Webhook secret from project creation (whsec_xxx).
        timestamp: Value of X-PayzCore-Timestamp header (required).
        tolerance_seconds: Max age in seconds (default: 300 = 5 minutes).

    Returns:
        True if signature is valid, False otherwise.
    """
    if not secret or not signature or not body:
        return False

    # Timestamp is required for signature verification
    if not timestamp:
        return False

    # Replay protection: reject stale webhooks
    from datetime import datetime, timezone

    try:
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = abs((now - ts).total_seconds())
        if diff > tolerance_seconds:
            return False
    except (ValueError, TypeError):
        return False

    # Signature covers timestamp + body
    message = f"{timestamp}.".encode() + body.encode("utf-8")
    expected = hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def parse_webhook(body: str) -> WebhookPayload:
    """Parse a raw webhook body into a typed WebhookPayload.

    Logs warnings for unknown network/token values (forward-compatible).

    Args:
        body: Raw request body string (JSON).

    Returns:
        Parsed webhook payload.
    """
    raw: Dict[str, Any] = json.loads(body)

    network = raw.get("network", "")
    if network and network not in SUPPORTED_NETWORKS:
        logger.warning("[PayzCore] Unknown network in webhook: %s", network)

    token = raw.get("token", "")
    if token and token not in SUPPORTED_TOKENS:
        logger.warning("[PayzCore] Unknown token in webhook: %s", token)

    payload: WebhookPayload = {
        "event": raw["event"],
        "payment_id": raw["payment_id"],
        "external_ref": raw["external_ref"],
        "network": raw["network"],
        "token": raw.get("token", "USDT"),
        "address": raw["address"],
        "expected_amount": raw["expected_amount"],
        "paid_amount": raw["paid_amount"],
        "tx_hash": raw.get("tx_hash"),
        "status": raw["status"],
        "paid_at": raw.get("paid_at"),
        "metadata": raw.get("metadata", {}),
        "timestamp": raw["timestamp"],
    }
    if raw.get("external_order_id") is not None:
        payload["external_order_id"] = raw["external_order_id"]
    # Payment link buyer fields (only present for payment link payments)
    if raw.get("buyer_email") is not None:
        payload["buyer_email"] = raw["buyer_email"]
    if raw.get("buyer_name") is not None:
        payload["buyer_name"] = raw["buyer_name"]
    if raw.get("buyer_note") is not None:
        payload["buyer_note"] = raw["buyer_note"]
    if raw.get("payment_link_id") is not None:
        payload["payment_link_id"] = raw["payment_link_id"]
    if raw.get("payment_link_slug") is not None:
        payload["payment_link_slug"] = raw["payment_link_slug"]

    return payload


def construct_event(
    body: str,
    signature: str,
    secret: str,
    timestamp: Optional[str] = None,
    tolerance_seconds: int = 300,
) -> WebhookPayload:
    """Verify signature and parse the webhook payload.

    Args:
        body: Raw request body string.
        signature: Value of X-PayzCore-Signature header.
        secret: Webhook secret from project creation (whsec_xxx).
        timestamp: Value of X-PayzCore-Timestamp header (required).
        tolerance_seconds: Max age in seconds (default: 300 = 5 minutes).

    Returns:
        Parsed and typed webhook payload.

    Raises:
        WebhookSignatureError: If signature verification fails.
    """
    if not verify_signature(body, signature, secret, timestamp, tolerance_seconds):
        raise WebhookSignatureError()

    try:
        return parse_webhook(body)
    except json.JSONDecodeError:
        raise WebhookSignatureError("Invalid webhook payload")
