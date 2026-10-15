# Changelog

## 1.0.3 — 2026-10-15

### Fixed
- `payments.create()` raised `KeyError: 'existing'` for every **new** payment (the API only sends `existing` when it returns an existing payment). The payment was created server-side but the caller never got it. `existing` is now `False` when absent.
- `projects.list()` raised `KeyError: 'api_key'`. The API returns `api_key_prefix` (full keys are never listed); items now have `api_key_prefix`.
- `parse_webhook()` / `construct_event()` no longer fail when `network`, `token` or `address` are missing; they are `None` when the customer never selected a network. `token` no longer defaults to `"USDT"`.
- `POST` requests are retried only when they carry `external_order_id`, so a retry after a lost response can no longer create a duplicate payment.
- Version strings: `__version__` and the User-Agent now report the real version (were `1.0.0`).
- PyPI "Changelog" link pointed to a 404 page.

### Added
- `payments.list()` returns `pagination` (`total`, `limit`, `offset`, `has_more`) and accepts `created_after` / `updated_after`.
- List items include `updated_at`; `payments.get()` includes `paid_at`; `available_networks[]` include `confirmations` and `explorer`.

### Changed
- `IdempotencyError` is raised for every HTTP 409 and its default message is now `Conflict`; read `message` for the reason.
- Documented that `RateLimitError.retry_after` is an absolute Unix timestamp (from `X-RateLimit-Reset`), not a number of seconds.

## 1.0.2 — 2026-03-01

- Webhook signature now covers `timestamp + "." + body`; `timestamp` is required for verification.
