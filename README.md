# PayzCore Python SDK

Python client for the [PayzCore](https://payzcore.com) blockchain transaction monitoring API.

## Important

**PayzCore is a blockchain monitoring service, not a payment processor.** All payments are sent directly to your own wallet addresses. PayzCore never holds, transfers, or has access to your funds.

- **Your wallets, your funds** — You provide your own wallet (HD xPub or static addresses). Customers pay directly to your addresses.
- **Read-only monitoring** — PayzCore watches the blockchain for incoming transactions and sends webhook notifications. That's it.
- **Protection Key security** — Sensitive operations like wallet management, address changes, and API key regeneration require a Protection Key that only you set. PayzCore cannot perform these actions without your authorization.
- **Your responsibility** — You are responsible for securing your own wallets and private keys. PayzCore provides monitoring and notification only.

## Installation

```bash
pip install payzcore
```

## Quick Start

### Payment Monitoring

```python
from payzcore import PayzCore

client = PayzCore("pk_live_xxx")

# Create a payment monitoring request (network specified)
response = client.payments.create(
    amount=50,
    external_ref="user-123",
    network="TRC20",
)
payment = response["payment"]
print(f"Send {payment['amount']} {payment['token']} to {payment['address']}")
print(f"Expires at: {payment['expires_at']}")
# Static wallet projects may also return: payment['notice'], payment['original_amount'], payment['requires_txid']

# Or let the customer choose the network on the payment page
response = client.payments.create(
    amount=50,
    external_ref="user-123",
)
p = response["payment"]
print(p["awaiting_network"])    # True
print(p["payment_url"])         # "https://app.payzcore.com/pay/xxx"
print(p["available_networks"])  # [{"network": "TRC20", "name": "Tron", "tokens": ["USDT"]}, ...]

# Create a USDC payment on Polygon
response = client.payments.create(
    amount=100,
    external_ref="order-456",
    network="POLYGON",
    token="USDC",
)

# Create a payment with static wallet (dedicated mode)
response = client.payments.create(
    amount=50,
    external_ref="user-789",
    network="TRC20",
    address="Txxxx...",  # optional, static wallet dedicated mode only
)

# List payments
payments = client.payments.list(status="pending", limit=10)
for p in payments["payments"]:
    print(f"{p['id']}: {p['status']} ({p['expected_amount']} {p['token']})")

# Get payment details (latest cached status from database)
detail = client.payments.get("payment-uuid")
print(f"Status: {detail['payment']['status']}")
for tx in detail["payment"]["transactions"]:
    print(f"  TX: {tx['tx_hash']} - {tx['amount']} {detail['payment']['token']}")

# Cancel a pending payment
result = client.payments.cancel("payment-uuid")
# result["payment"]["status"] == "cancelled"

# Submit tx hash for verification (pool + txid mode)
result = client.payments.confirm("payment-uuid", "abc123def456...")
# result["verified"], result["status"], result["amount_received"]
```

### Supported Networks and Tokens

| Network | Blockchain | Tokens |
|---------|------------|--------|
| `TRC20` | Tron | USDT |
| `BEP20` | BNB Smart Chain | USDT, USDC |
| `ERC20` | Ethereum | USDT, USDC |
| `POLYGON` | Polygon | USDT, USDC |
| `ARBITRUM` | Arbitrum | USDT, USDC |

The `token` parameter defaults to `"USDT"` if not specified, ensuring backward compatibility.

### Project Management (Admin)

```python
from payzcore import PayzCore

admin = PayzCore("mk_xxx", master_key=True)

# Create a project
project = admin.projects.create(
    name="My Store",
    slug="my-store",
    webhook_url="https://example.com/webhooks/payzcore",
)
print(f"API Key: {project['project']['api_key']}")

# List projects
projects = admin.projects.list()
for p in projects["projects"]:
    print(f"{p['name']} ({p['slug']}): {'active' if p['is_active'] else 'inactive'}")
```

### Webhook Verification

```python
from payzcore import verify_signature, construct_event, WebhookSignatureError

# In your webhook handler
def handle_webhook(request):
    body = request.body.decode("utf-8")
    signature = request.headers["X-PayzCore-Signature"]
    secret = "whsec_xxx"  # From project creation

    try:
        event = construct_event(body, signature, secret)
    except WebhookSignatureError:
        return {"error": "Invalid signature"}, 401

    if event["event"] == "payment.completed":
        print(f"Payment {event['payment_id']} completed!")
        print(f"Amount: {event['paid_amount']} {event['token']} on {event['network']}")

    return {"ok": True}, 200
```

> **Note:** The `address` parameter is only used with static wallet projects in dedicated mode. For HD wallet projects, this parameter is ignored.

## Static Wallet Mode

When the PayzCore project is configured with a static wallet, the API works the same way but may return additional fields in the response:

| Field | Type | Description |
|-------|------|-------------|
| `notice` | `str` | Instructions for the payer (e.g. "Send exact amount") |
| `original_amount` | `str` | The original requested amount before any adjustments |
| `requires_txid` | `bool` | Whether the payer must submit their transaction ID |

In dedicated address mode, you can specify which static address to assign to a customer using the `address` parameter on payment creation. In shared address mode, the project's single static address is used automatically.

## Before Going Live

**Always test your setup before accepting real payments:**

1. **Verify your xPub** — In the PayzCore dashboard, click "Verify Key" when adding your wallet. Compare address #0 with your wallet app's first receiving address. They must match.
2. **Send a test payment** — Create a monitoring request for $1–5 and send the funds to the assigned address. Verify they arrive in your wallet.
3. **Test sweeping** — Send the test funds back out to confirm you control the derived addresses with your private keys.

> **Warning:** A wrong xPub key generates addresses you don't control. Funds sent to those addresses are permanently lost. PayzCore is watch-only and cannot recover funds. Please take 2 minutes to verify.

## Configuration

```python
client = PayzCore(
    "pk_live_xxx",
    base_url="https://api.payzcore.com",  # API base URL
    timeout=30.0,                          # Request timeout (seconds)
    max_retries=2,                         # Retries on 5xx errors
    master_key=False,                      # Use x-master-key header
)
```

## Error Handling

```python
from payzcore import (
    PayzCore,
    PayzCoreError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NotFoundError,
)

client = PayzCore("pk_live_xxx")

try:
    payment = client.payments.create(
        amount=50, network="TRC20", external_ref="user-123"
    )
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Invalid params: {e.message}")
    if e.details:
        for d in e.details:
            print(f"  {d['path']}: {d['message']}")
except RateLimitError as e:
    print(f"Rate limited. Daily: {e.is_daily}, retry after: {e.retry_after}")
except NotFoundError:
    print("Resource not found")
except PayzCoreError as e:
    print(f"API error {e.status}: {e.message}")
```

### Error Classes

| Class | Status | When |
|-------|--------|------|
| `AuthenticationError` | 401 | Invalid/missing API key |
| `ForbiddenError` | 403 | Project deactivated |
| `NotFoundError` | 404 | Payment/resource not found |
| `ValidationError` | 400 | Invalid request body |
| `RateLimitError` | 429 | Rate limit or daily plan limit exceeded |
| `IdempotencyError` | 409 | `external_order_id` reused with different `external_ref` |
| `WebhookSignatureError` | — | Invalid webhook signature |

## Requirements

- Python 3.9+
- httpx

## See Also

- [Getting Started](https://docs.payzcore.com/getting-started) — Account setup and first payment
- [Authentication & API Keys](https://docs.payzcore.com/guides/authentication) — API key management
- [Webhooks Guide](https://docs.payzcore.com/guides/webhooks) — Events, headers, and signature verification
- [Supported Networks](https://docs.payzcore.com/guides/networks) — Available networks and tokens
- [Error Reference](https://docs.payzcore.com/guides/errors) — HTTP status codes and troubleshooting
- [API Reference](https://docs.payzcore.com) — Interactive API documentation (Scalar UI)

## License

MIT
