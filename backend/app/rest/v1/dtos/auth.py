from backend.internal.dto import StructDTO

from .users import User


class AuthContext[T](StructDTO):
    token: str
    data: T


class OAuthCallbackResult(StructDTO):
    """What an OAuth callback resolved to.

    ``setup_required`` means the provider returned no email, so no account was
    created: the caller must complete the two-step signup (completeSignup ->
    confirmSignup). ``user`` is populated only when a session was established.
    """

    setup_required: bool
    user: User | None = None


class OAuthCallbackOutcome(StructDTO):
    """Handler-internal envelope — the controller turns the tokens into cookies.

    Neither token is ever serialized to the client: ``session_token`` becomes the
    session cookie, ``setup_token`` the short-lived setup cookie.
    """

    result: OAuthCallbackResult
    session_token: str | None = None
    setup_token: str | None = None


class OAuthSignupChallenge(StructDTO):
    """Response to completeSignup — deliberately carries no account information.

    Byte-identical whether or not the address is already registered, so the
    endpoint cannot be used to enumerate accounts.
    """

    ttl_seconds: int
    cooldown_seconds: int


class SetupToken(StructDTO):
    setup_token: str


class ReauthToken(StructDTO):
    reauth_token: str


class DeliveryAck(StructDTO):
    """Neutral acknowledgment for a code/link request.

    Byte-identical whether or not an account exists for the identifier, so the
    endpoint cannot be used to enumerate accounts (the enumeration-safe default).
    A project that instead wants to reveal existence to offer signup can re-add an
    ``account_exists`` flag on the email path — see the swap point in docs/AUTH.md.
    """

    sent: bool = True


class UsernameAvailability(StructDTO):
    available: bool
    reason: str
    sanitized: str
