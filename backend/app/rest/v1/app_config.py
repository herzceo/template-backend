from backend.internal.dto import StructDTO


class AppConfig(StructDTO):
    """Public site root used to build absolute links a human clicks.

    ``APP_PUBLIC_URL`` is the frontend/site root (e.g. ``https://app.example.com``)
    that the password-reset email, the change-email confirmation link, and the
    OAuth settings link are built from. It defaults to empty so the template runs
    with no extra required env — set it in production so emailed links are
    absolute. A dependency-free leaf module (not under ``handlers/``) so it can be
    injected without an import cycle through the eagerly-imported handler packages.
    """

    APP_PUBLIC_URL: str = ""

    @property
    def public_base(self) -> str:
        """Site root without a trailing slash."""
        return self.APP_PUBLIC_URL.rstrip("/")


class RateLimitConfig(StructDTO):
    """Fixed-window throttle for the public auth request endpoints (per IP).

    Guards the unauthenticated code/link/email-issuing endpoints against
    email-bombing and unbounded lookups. Env-overridable; the defaults allow a
    small burst per minute per IP.
    """

    AUTH_RATE_LIMIT: int = 5
    AUTH_RATE_WINDOW_SECONDS: int = 60
