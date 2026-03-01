"""Payments resource for PayzCore API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ..client import HttpClient
from ..types import (
    CancelPaymentResponse,
    ConfirmPaymentResponse,
    CreatePaymentResponse,
    GetPaymentResponse,
    ListPaymentsResponse,
    Payment,
    PaymentDetail,
    PaymentListItem,
    PaymentStatus,
    Token,
    Transaction,
)


def _map_payment(raw: Dict[str, Any]) -> Payment:
    result: Payment = {
        "id": raw["id"],
        "address": raw.get("address"),
        "amount": raw["amount"],
        "network": raw.get("network"),
        "token": raw.get("token"),
        "status": raw["status"],
        "expires_at": raw["expires_at"],
    }
    if raw.get("external_order_id") is not None:
        result["external_order_id"] = raw["external_order_id"]
    if raw.get("qr_code") is not None:
        result["qr_code"] = raw["qr_code"]
    if raw.get("notice") is not None:
        result["notice"] = raw["notice"]
    if raw.get("original_amount") is not None:
        result["original_amount"] = raw["original_amount"]
    if raw.get("requires_txid") is not None:
        result["requires_txid"] = raw["requires_txid"]
    if raw.get("confirm_endpoint") is not None:
        result["confirm_endpoint"] = raw["confirm_endpoint"]
    if raw.get("awaiting_network") is not None:
        result["awaiting_network"] = raw["awaiting_network"]
    if raw.get("payment_url") is not None:
        result["payment_url"] = raw["payment_url"]
    if raw.get("available_networks") is not None:
        result["available_networks"] = raw["available_networks"]
    return result


def _map_payment_list_item(raw: Dict[str, Any]) -> PaymentListItem:
    result: PaymentListItem = {
        "id": raw["id"],
        "external_ref": raw["external_ref"],
        "network": raw.get("network"),
        "token": raw.get("token"),
        "address": raw.get("address"),
        "expected_amount": raw["expected_amount"],
        "paid_amount": raw["paid_amount"],
        "status": raw["status"],
        "tx_hash": raw.get("tx_hash"),
        "expires_at": raw["expires_at"],
        "paid_at": raw.get("paid_at"),
        "created_at": raw["created_at"],
    }
    if raw.get("external_order_id") is not None:
        result["external_order_id"] = raw["external_order_id"]
    return result


def _map_transaction(raw: Dict[str, Any]) -> Transaction:
    return {
        "tx_hash": raw["tx_hash"],
        "amount": raw["amount"],
        "from_address": raw["from"],
        "confirmed": raw["confirmed"],
        "confirmations": raw.get("confirmations", 0),
    }


def _map_payment_detail(raw: Dict[str, Any]) -> PaymentDetail:
    txs = raw.get("transactions", [])
    result: PaymentDetail = {
        "id": raw["id"],
        "status": raw["status"],
        "expected_amount": raw["expected_amount"],
        "paid_amount": raw["paid_amount"],
        "address": raw.get("address"),
        "network": raw.get("network"),
        "token": raw.get("token"),
        "tx_hash": raw.get("tx_hash"),
        "expires_at": raw["expires_at"],
        "transactions": [_map_transaction(t) for t in txs],
    }
    if raw.get("awaiting_network") is not None:
        result["awaiting_network"] = raw["awaiting_network"]
    return result


class Payments:
    """Payments resource."""

    def __init__(self, client: HttpClient) -> None:
        self._client = client

    def create(
        self,
        *,
        amount: float,
        external_ref: str,
        network: Optional[str] = None,
        token: Optional[str] = None,
        external_order_id: Optional[str] = None,
        address: Optional[str] = None,
        expires_in: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CreatePaymentResponse:
        """Create a new payment monitoring request.

        Args:
            amount: Payment amount in stablecoin.
            external_ref: Your reference ID for this payment.
            network: Blockchain network. If omitted, customer selects on the payment page.
            token: Stablecoin token ("USDT" or "USDC"). Default: "USDT".
            external_order_id: Optional order ID for idempotency.
            address: Pre-assign a specific static address for this customer (dedicated mode only).
            expires_in: Expiry in seconds (300-86400). Default: 3600.
            metadata: Optional metadata dict.

        Returns:
            CreatePaymentResponse with payment details and deposit address.
        """
        body: Dict[str, Any] = {
            "amount": amount,
            "external_ref": external_ref,
        }
        if network is not None:
            body["network"] = network
        if token is not None:
            body["token"] = token
        if external_order_id is not None:
            body["external_order_id"] = external_order_id
        if address is not None:
            body["address"] = address
        if expires_in is not None:
            body["expires_in"] = expires_in
        if metadata is not None:
            body["metadata"] = metadata

        raw = self._client.post("/v1/payments", body)
        return {
            "success": True,
            "existing": raw["existing"],
            "payment": _map_payment(raw["payment"]),
        }

    def list(
        self,
        *,
        status: Optional[PaymentStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListPaymentsResponse:
        """List payments for the project.

        Args:
            status: Filter by payment status.
            limit: Max results to return.
            offset: Pagination offset.

        Returns:
            ListPaymentsResponse with list of payments.
        """
        params: Dict[str, str] = {}
        if status is not None:
            params["status"] = status
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)

        qs = urlencode(params)
        path = f"/v1/payments?{qs}" if qs else "/v1/payments"
        raw = self._client.get(path)
        return {
            "success": True,
            "payments": [_map_payment_list_item(p) for p in raw["payments"]],
        }

    def get(self, payment_id: str) -> GetPaymentResponse:
        """Get payment details (latest cached status from database).

        Args:
            payment_id: The payment UUID.

        Returns:
            GetPaymentResponse with full payment details and transactions.
        """
        from urllib.parse import quote

        raw = self._client.get(f"/v1/payments/{quote(payment_id, safe='')}")
        return {
            "success": True,
            "payment": _map_payment_detail(raw["payment"]),
        }

    def cancel(self, payment_id: str) -> CancelPaymentResponse:
        """Cancel a pending payment.

        Args:
            payment_id: The payment UUID. Must be in 'pending' status.

        Returns:
            CancelPaymentResponse with cancelled payment details.
        """
        from urllib.parse import quote

        raw = self._client.patch(
            f"/v1/payments/{quote(payment_id, safe='')}",
            {"status": "cancelled"},
        )
        return {
            "success": True,
            "payment": raw["payment"],
        }

    def confirm(self, payment_id: str, tx_hash: str) -> ConfirmPaymentResponse:
        """Submit a transaction hash for verification (pool + txid mode only).

        Args:
            payment_id: The payment UUID.
            tx_hash: Blockchain transaction hash (hex digits only, no 0x prefix).

        Returns:
            ConfirmPaymentResponse with verification status.
        """
        from urllib.parse import quote

        raw = self._client.post(
            f"/v1/payments/{quote(payment_id, safe='')}/confirm",
            {"tx_hash": tx_hash},
        )
        return {
            "success": True,
            "status": raw["status"],
            "verified": raw["verified"],
            "amount_received": raw.get("amount_received"),
            "amount_expected": raw.get("amount_expected"),
            "message": raw.get("message"),
        }
