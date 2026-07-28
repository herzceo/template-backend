# Authentication

This template ships a complete, cookie-session auth system with password login,
passwordless email codes, OAuth (Google / GitHub / Discord), a two-step OAuth
signup for providers that return no email, password reset / set / change, one-time
username selection, email change, identity linking, and step-up re-authentication.

It is deliberately built from small, swappable seams so a fork can keep the parts
it needs and drop the rest. The "Swap points" section at the end names each seam.

## Model

### Session (the only long-lived credential)
A successful login mints a **server-side `Session` row** and returns an opaque
token in an **httpOnly `session` cookie**. `SessionMiddleware`
(`entry/rest/common/middlewares/session.py`) resolves the cookie on every
non-`exclude_from_auth` route and puts a `Session` DTO on `scope["auth"]`; a
controller reads the caller as `request.auth.user_id` / `request.auth.id`. Tokens
are stored **hashed** (`SecretTokenGenerator`); the raw token lives only in the
cookie. TTL is `SessionConfig.SESSION_TTL_DAYS` (14).

### Redis-backed codes & tokens (all short-lived, hash-only)
None of the "tokens" below are DB rows — they live in Redis behind ports in
`app/shared/ports/security/`:

| Port | Purpose | Key facts |
|---|---|---|
| `VerificationCodeStore` | email-verification / OAuth-signup codes | 6-digit, TTL 15m, `max_attempts` 3, attempts reset on expiry |
| `LoginCodeStore` | passwordless "magic code" login | separate namespace + attempt counter from verification |
| `OneTimeTokenStore` | password-reset, signup-setup, and reauth tokens | single-use, hash-only, atomic `consume` — a replay resolves to `None` |
| `OAuthSetupStore` | the entire in-flight no-email OAuth signup (`OAuthSetupSession`) | hash-only token in the `oauth_setup` httpOnly cookie; lifetime-preserving `update` |
| `RateLimiter` | fixed-window per-IP throttle | **enforced** on the public request endpoints (see below) |

Raw codes/tokens are **never** persisted — only their hashes. The one-time tokens
carry a `purpose` (`OTT_PURPOSE_PASSWORD_RESET` / `_SIGNUP_SETUP` / `_REAUTH`) so a
token minted for one flow can never be consumed by another.

### `UserEmail` — the global email-uniqueness index
`domain/entities/user_email.py` is the single authority that keeps every email a
user owns (their primary + each OAuth provider's reported email) unique **across
all accounts together**, via a global unique index on `normalized_email`.
`EmailNormalizer.canonical()` produces that key (lowercases, and for Gmail strips
`+tags` and dots) — the same canonical form the migration backfills, so lookups
and backfilled rows always agree. `IdentityService.register_email` /
`email_owner_id` are the only paths that write/read it; the DB unique constraint
is the race backstop (an `IntegrityError` surfaces as `AlreadyExistsError`).

### `username_confirmed` / `needs_username`
`User.username_confirmed` gates the one-time choose-username step. Email/password
signups pick a username up front → `True`. A fresh OAuth account that carried an
email gets an auto-generated handle → `False`, and `needs_username` is `True`
until the user confirms one at `chooseUsername` (immutable thereafter).

## Flows

- **Password login** — `POST /auth/signIn {username|email, password}`. Verifies
  the password identity, requires a verified account, mints a session.
- **Signup** — `POST /auth/signUp {username, email, password, tenant_id}`. Creates
  `User` + `Profile` + a primary `UserEmail` (unverified) + two password
  identities, and publishes `UserVerificationRequested` (the neutral extension
  seam — a project subscribes to it to grant plans/credits/etc.).
- **Verify email** — `POST /auth/verifyEmail {email, code}` → verifies + logs in.
  `POST /auth/resendVerification` re-issues under a resend cooldown.
- **Email-code login (passwordless)** — `POST /auth/loginCodeRequest {identifier}`
  → neutral `DeliveryAck`; the code is emailed only for a verified account and
  only outside the cooldown. `POST /auth/loginCodeVerify {identifier, code}` →
  session.
- **Password reset** — `POST /auth/passwordResetRequest {identifier}` → neutral
  `DeliveryAck` (emails a one-time link only for a real account). `POST
  /auth/passwordResetConfirm {token, password}` consumes the token, sets both
  password identities, verifies the account, logs in.
- **First password (post no-email OAuth signup path variant)** — `POST
  /auth/setPassword {password}` with the `oauth_setup` cookie: consumes the
  signup-setup token, sets the password, logs in.
- **Change password** — `POST /auth/changePassword {reauth_token, new_password}`
  (authed) — requires a fresh reauth token (see step-up).
- **Choose username** — `GET /auth/usernameAvailable?username=` for live
  validation; `POST /auth/chooseUsername {username}` (authed) — allowed once,
  while `username_confirmed` is `False`.
- **Change email** — `POST /auth/changeEmailRequest {reauth_token, new_email}`
  (authed) emails a signed confirmation link to the **new** address; `POST
  /auth/changeEmailConfirm {token}` moves the primary email + `UserEmail` row and
  rekeys the email/password identity.
- **OAuth login / auto-link** — `GET /auth/oauth/initiate?provider=` → authorize
  URL; the frontend returns `code`/`state` to `POST
  /auth/oauth/{provider}/callback`. An existing identity logs in; a new identity
  **with** a provider email auto-links to the account that owns that email, else
  creates one (auto username, `username_confirmed=False`).
- **Two-step OAuth signup (no provider email)** — the callback returns
  `OAuthCallbackResult{setup_required=True}` and sets the `oauth_setup` cookie,
  creating **nothing**. `POST /auth/oauth/completeSignup {email, username}` stashes
  them and emails a code (byte-identical response regardless of account
  existence); `POST /auth/oauth/confirmSignup {code}` proves the address, then —
  and only then — creates the account or attaches the identity to the owner.
- **Identity linking** (authed) — `GET /auth/identities`; `GET
  /auth/link/oauth/initiate?provider=` + `POST
  /auth/link/oauth/{provider}/callback` (never switches accounts — errors
  `provider_already_linked` if the identity is someone else's); `POST
  /auth/identities/{provider}/unlink` (refuses to remove the last sign-in method).
- **Step-up reauth** — `POST /auth/reauth/password {password}` or the OAuth
  variant (`/auth/reauth/oauth/initiate` + `/auth/reauth/oauth/{provider}/callback`)
  mints a short-lived `ReauthToken` consumed by the sensitive changes
  (change email / change password).
- **Session** — `POST /auth/signOut` revokes the session; `GET /me` returns the
  current user.

## Security posture (do not weaken)

- **Email enumeration.** `loginCodeRequest`, `passwordResetRequest`, and
  `completeSignup` return **byte-identical** responses whether or not the account
  exists — this is the honest, conservative default. `resolve_user_by_identifier`
  swallows a malformed identifier to `Option(None)`; these endpoints return
  **200, never 404**.
- **Code brute-force.** Attempt cap (`max_attempts` = 3), attempts reset on
  expiry, `retry_after_seconds` surfaced via `too_many_attempts_error`.
- **Token entropy & replay.** Codes are 6-digit `secrets.randbelow` (short TTL +
  attempt cap compensate). One-time / setup tokens are `SecretTokenGenerator`
  values stored **as hash only**, single-use, atomically consumed.
- **OAuth setup device binding.** `check_setup_device` softly binds a setup
  session to its originating device fingerprint (both present-and-different →
  reject; any `None` passes, so ad-blocked clients aren't stranded).
- **OAuth state / step-up isolation.** Signed `oauth_state` wraps login, link, and
  reauth; a `link|` / `reauth|` state can never drive the login/signup callback
  (that would be an account switch).
- **Unlink lockout.** `unlink_identity` refuses to remove the only remaining
  sign-in method.
- **Rate limiting (enforced).** The four public request endpoints
  (`loginCodeRequest`, `passwordResetRequest`, `changeEmailRequest`,
  `completeSignup`) throttle **per IP** via `RateLimiter.hit` before any user
  lookup — so the decision never leaks account existence — with defaults from
  `RateLimitConfig` (`AUTH_RATE_LIMIT=5` / `AUTH_RATE_WINDOW_SECONDS=60`,
  env-overridable). Over-limit → `rate_limited` with `retry_after_seconds`. This
  caps the email-bombing / unbounded-lookup vector on the unauthenticated
  endpoints.
- **Credential-change invalidation.** A password reset or change revokes **all**
  the user's sessions (`session_.delete_by_user_id`) and drops any pending
  login/verification code, so a compromised session or a pre-issued code can't
  outlive the change.

## Swap points (adapting the template to a different auth model)

Each is a named seam — change it in one place.

- **No-password / passwordless-only.** Drop the `login` / `set_password` /
  `change_password` handlers and password reset; keep `login_code_*` and OAuth.
  Signup then never creates password identities.
- **B2B SSO-only.** Keep OAuth + `link_*`; remove `signup`, the email-code, and the
  password handlers; make the OAuth gateway the sole entry.
- **Tenant-scoped auth.** Make `UserEmail.normalized_email` a **composite unique
  index `(tenant_id, normalized_email)`** (add `tenant_id` to the entity + the
  migration) and scope `resolve_user_by_identifier` / `email_owner_id` by tenant.
- **Custom email delivery.** Swap the `EmailSender` adapter
  (`infra/external/adapters/email/`) and/or the `.html` templates. The template
  ships `.html`-only (no `.txt`); the neutral copy uses no brand token — replace
  it with your own.
- **Custom email normalization.** Replace `ImplEmailNormalize`
  (`infra/external/adapters/email_normalizer.py`) with a deeper provider-aware
  canonicalizer (e.g. an `email-normalize`/MX-backed one) — **keep the migration's
  `_canonical` backfill SQL in sync** with whatever canonical form it produces.
- **Custom human-check (captcha / bot gate).** There is a deliberate no-op seam:
  the template ships **no** captcha/abuse gating. Add it by injecting a check into
  `signup` / the OAuth callback (a config flag defaulting off, so the template
  stays clean and a fork opts in without the base shipping it).
- **Rate-limit tuning.** Rate limiting is **on by default** (see the security
  posture section). Tune it via `RateLimitConfig` env vars, or reimplement the
  `RateLimiter` port over a different backend; add per-account keying alongside
  the per-IP key in the four request handlers if you want it.
- **Opt-in "reveal existence to offer signup" (non-neutral enumeration).** The
  neutral `DeliveryAck` is the default. A project that wants the UI to offer signup
  when an **email** has no account can re-add an `account_exists` flag (and a
  machine `reason` code) to `DeliveryAck` and set it on the email path of
  `loginCodeRequest` — a deliberate, documented departure from neutrality. Never
  do it on the username path (collapse "no such username" and "exists but
  unverified" into one response).
- **Different code/token stores.** Reimplement the four Redis ports
  (`LoginCodeStore`, `OneTimeTokenStore`, `OAuthSetupStore`, `RateLimiter`) over a
  different backend (DB, external cache) — the ports are the seam; the handlers
  don't change.
- **A different auth model entirely.** If none of the above fit (e.g. mTLS,
  hardware keys, a third-party IdP that owns sessions), the stable contract is:
  a handler mints a session via `SessionService.create_session` and returns
  `AuthContext(token, data)`; the controller sets the cookie via
  `set_session_token`. Build your entry path to that contract and reuse the
  session/`UserEmail`/identity model underneath, or replace `SessionService`
  itself and keep the controller/middleware seam.
