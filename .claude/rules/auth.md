---
paths:
  - "backend/app/rest/v1/handlers/auth/**/*.py"
  - "backend/app/shared/ports/security/**/*.py"
  - "backend/infra/database/redis/adapters/**/*.py"
  - "backend/entry/rest/v1/auth.py"
  - "backend/domain/entities/user_email.py"
---

# Auth Rules

Cookie-session auth built from small swappable seams. Full flow map + endpoint
list lives in the code (`entry/rest/v1/auth.py`); this is the policy you hold
when touching any of it.

## Model — the building blocks

- **Session** is the only long-lived credential. Login mints a server-side
  `Session` row, returns an opaque token in an httpOnly `session` cookie stored
  **hashed** (`SecretTokenGenerator`); `SessionMiddleware` resolves it onto
  `request.auth`. TTL `SESSION_TTL_DAYS` (14).
- **Redis-backed codes/tokens** are short-lived and hash-only, behind ports in
  `app/shared/ports/security/`: `VerificationCodeStore` (email/OAuth-signup
  codes), `LoginCodeStore` (passwordless), `OneTimeTokenStore` (reset /
  signup-setup / reauth — carries a `purpose` so a token for one flow can't be
  consumed by another), `OAuthSetupStore` (in-flight no-email OAuth signup),
  `RateLimiter`. Adapters in `infra/database/redis/adapters/`.
- **`UserEmail`** (`domain/entities/user_email.py`) is the global
  email-uniqueness index: a unique index on `normalized_email` keeps every email
  a user owns unique across *all* accounts. `EmailNormalizer.canonical()`
  produces the key; the migration backfills the same form — keep them in sync.
- **`username_confirmed` / `needs_username`** gate the one-time choose-username
  step: password signups pick up front (`True`); a fresh OAuth account gets an
  auto handle (`False`) until it confirms one (immutable after).

## Flows at a glance

Password login + signup + email verify; passwordless email-code login; password
reset / set (post no-email OAuth) / change; username availability + choose;
email change (request→confirm); OAuth login with auto-link; two-step OAuth signup
for providers with no email; identity link / list / unlink; step-up reauth
(password or OAuth) gating the sensitive changes; signOut + `GET /me`. Handlers
auto-register via `handlers.get_defined_rest_handlers()` — a new one needs only
its file + `__init__` export.

## Security invariants — do NOT weaken

- **Enumeration-safe.** `loginCodeRequest`, `passwordResetRequest`,
  `changeEmailRequest`, `completeSignup` return **byte-identical** responses
  (`DeliveryAck`) whether or not the account exists — **200, never 404**. A code
  is emailed only for a real, verified account, only outside cooldown.
- **Per-IP rate limit is on by default.** The four request endpoints call
  `RateLimiter.hit` **before** any user lookup (so the decision can't leak
  existence). Defaults from `RateLimitConfig` (`AUTH_RATE_LIMIT=5` /
  `AUTH_RATE_WINDOW_SECONDS=60`); over-limit → `rate_limited` + `retry_after`.
- **Brute-force cap.** Codes are 6-digit `secrets.randbelow`; `max_attempts=3`,
  attempts reset on expiry, `retry_after_seconds` via `too_many_attempts_error`.
- **Hash-only, single-use tokens.** Codes/one-time/setup tokens are persisted as
  hash only; one-time tokens are atomically consumed — a replay resolves to
  `None`.
- **OAuth state = CSRF guard.** Signed `oauth_state` wraps login / link / reauth;
  a `link|` or `reauth|` state can never drive the login/signup callback (that
  would be an account switch). Setup sessions softly bind to a device
  fingerprint (both present-and-different → reject; any `None` passes).
- **Unlink-last-method guard.** `unlink_identity` refuses to remove the only
  remaining sign-in method.
- **Credential-change invalidation.** A password reset/change revokes **all** the
  user's sessions and drops pending login/verification codes.
- **Short reauth window.** Change-email / change-password require a fresh
  `ReauthToken` (one-time, short TTL) minted by a step-up reauth handler.

## Swap points (named seams — change in one place)

- **Passwordless-only** — drop `login` / `set_password` / `change_password` +
  reset; keep `login_code_*` + OAuth; signup stops creating password identities.
- **B2B SSO-only** — keep OAuth + `link_*`; remove signup, email-code, password
  handlers; OAuth gateway becomes the sole entry.
- **Tenant-scoped** — make `UserEmail.normalized_email` a composite unique
  `(tenant_id, normalized_email)` (entity + migration) and scope
  `resolve_user_by_identifier` / `email_owner_id` by tenant.
- **Custom email delivery / normalization** — swap the `EmailSender` adapter
  or `.html` templates; swap `ImplEmailNormalize` (keep the migration's
  `_canonical` backfill in sync with any new canonical form).
- **Custom human-check** — deliberate no-op seam (no captcha shipped); inject a
  check into `signup` / the OAuth callback behind a config flag defaulting off.
- **Opt-in existence-reveal** — the neutral `DeliveryAck` is the default; a fork
  may re-add an `account_exists` flag on the **email** path of `loginCodeRequest`
  only — never the username path.
- **Rate-limit tuning** — via `RateLimitConfig` env vars, or reimplement the
  `RateLimiter` port; add per-account keying alongside per-IP if wanted.
- **Different stores / model entirely** — the four Redis ports are the backend
  seam; the deeper contract is: a handler mints a session via
  `SessionService.create_session` and returns `AuthContext(token, data)`, the
  controller sets the cookie via `set_session_token`.
