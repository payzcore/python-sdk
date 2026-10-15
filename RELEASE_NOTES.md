# payzcore (Python) v1.0.3

**Upgrade recommended for everyone on 1.0.2.** In 1.0.2, `client.payments.create()` raised `KeyError: 'existing'` for every new payment, after the payment had already been created on the server.

```bash
pip install --upgrade payzcore==1.0.3
```

## Fixed
- `payments.create()` no longer raises `KeyError: 'existing'`; `existing` is `False` for new payments.
- `projects.list()` returns `api_key_prefix` (was a `KeyError` on `api_key`).
- Webhook parsing accepts `network` / `token` / `address` = `None`.
- No automatic retry of `POST` without `external_order_id` (prevents duplicate payments).
- `__version__`, User-Agent and the PyPI changelog link are correct.

## Added
- `payments.list(created_after=..., updated_after=...)` and `result["pagination"]`.
- `updated_at` on list items, `paid_at` on `payments.get()`.

## Notes
- `RateLimitError.retry_after` is an absolute Unix timestamp (unchanged behaviour, now documented).

Full changelog: [CHANGELOG.md](CHANGELOG.md) · Docs: https://docs.payzcore.com/sdks/python
