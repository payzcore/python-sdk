"""Regression tests for response mapping (run: python3 -m unittest discover -s tests)."""

from __future__ import annotations

import json
import unittest

import httpx

from payzcore import PayzCore, parse_webhook


def _client(handler) -> PayzCore:
    client = PayzCore("pk_live_test", base_url="https://api.test", max_retries=0)
    client._http_client._client = httpx.Client(transport=httpx.MockTransport(handler))
    return client


NEW_PAYMENT = {
    "success": True,
    "payment": {
        "id": "p1",
        "address": "Txxx",
        "amount": "50.07",
        "network": "TRC20",
        "token": "USDT",
        "status": "pending",
        "expires_at": "2026-10-15T12:00:00Z",
        "external_order_id": None,
        "qr_code": "data:image/png;base64,xx",
        "payment_url": "https://pay.payzcore.com/p1",
    },
}


class CreatePaymentTest(unittest.TestCase):
    def test_new_payment_without_existing_key(self) -> None:
        # The API omits "existing" for new payments (1.0.2 raised KeyError).
        client = _client(lambda req: httpx.Response(201, json=NEW_PAYMENT))
        res = client.payments.create(amount=50, external_ref="u1", network="TRC20")
        self.assertFalse(res["existing"])
        self.assertEqual(res["payment"]["id"], "p1")

    def test_existing_payment(self) -> None:
        body = dict(NEW_PAYMENT, existing=True)
        client = _client(lambda req: httpx.Response(200, json=body))
        res = client.payments.create(amount=50, external_ref="u1", network="TRC20")
        self.assertTrue(res["existing"])

    def test_post_without_idempotency_key_is_not_retried(self) -> None:
        calls = []

        def handler(req: httpx.Request) -> httpx.Response:
            calls.append(req)
            return httpx.Response(500, json={"error": "Failed to create payment"})

        client = PayzCore("pk_live_test", base_url="https://api.test", max_retries=2)
        client._http_client._client = httpx.Client(transport=httpx.MockTransport(handler))
        import payzcore.client as c

        c.RETRY_BASE_S = 0
        with self.assertRaises(Exception):
            client.payments.create(amount=50, external_ref="u1")
        self.assertEqual(len(calls), 1)


class ListTest(unittest.TestCase):
    def test_list_maps_updated_at_and_pagination(self) -> None:
        body = {
            "success": True,
            "payments": [
                {
                    "id": "p1",
                    "external_ref": "u1",
                    "external_order_id": None,
                    "network": "TRC20",
                    "token": "USDT",
                    "address": "Txxx",
                    "expected_amount": "50.07",
                    "paid_amount": "0",
                    "status": "pending",
                    "tx_hash": None,
                    "expires_at": "2026-10-15T12:00:00Z",
                    "paid_at": None,
                    "created_at": "2026-10-15T11:00:00Z",
                    "updated_at": "2026-10-15T11:05:00Z",
                }
            ],
            "pagination": {"total": 1, "limit": 50, "offset": 0, "has_more": False},
        }
        seen = {}

        def handler(req: httpx.Request) -> httpx.Response:
            seen["url"] = str(req.url)
            return httpx.Response(200, json=body)

        res = _client(handler).payments.list(updated_after="2026-10-15T00:00:00Z")
        self.assertIn("updated_after=2026-10-15T00%3A00%3A00Z", seen["url"])
        self.assertEqual(res["payments"][0]["updated_at"], "2026-10-15T11:05:00Z")
        self.assertEqual(res["pagination"]["total"], 1)

    def test_projects_list_uses_api_key_prefix(self) -> None:
        body = {
            "success": True,
            "total": 1,
            "limit": 100,
            "offset": 0,
            "projects": [
                {
                    "id": "pr1",
                    "name": "Store",
                    "slug": "store",
                    "api_key_prefix": "pk_live_ab",
                    "webhook_url": None,
                    "is_active": True,
                    "created_at": "2026-10-15T11:00:00Z",
                }
            ],
        }
        client = PayzCore("mk_test", base_url="https://api.test", master_key=True)
        client._http_client._client = httpx.Client(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
        )
        res = client.projects.list()
        self.assertEqual(res["projects"][0]["api_key_prefix"], "pk_live_ab")


class WebhookTest(unittest.TestCase):
    def test_parse_webhook_with_null_network_and_address(self) -> None:
        payload = {
            "event": "payment.cancelled",
            "payment_id": "p1",
            "external_ref": "u1",
            "network": None,
            "token": None,
            "address": None,
            "expected_amount": "50.00",
            "paid_amount": "0",
            "tx_hash": None,
            "status": "cancelled",
            "paid_at": None,
            "metadata": {},
            "timestamp": "2026-10-15T11:00:00.000Z",
        }
        event = parse_webhook(json.dumps(payload))
        self.assertIsNone(event["network"])
        self.assertIsNone(event["address"])


if __name__ == "__main__":
    unittest.main()
