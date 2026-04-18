import base64
import binascii
import hashlib
import hmac
import time
from typing import final

from backend.app.ports.oauth_state import OAuthStateSigner
from backend.internal import Option

_EXPECTED_PARTS = 3


@final
class ImplHMACOAuthStateSigner(OAuthStateSigner):
    def __init__(self, secret: str) -> None:
        self._secret = secret.encode()

    def _sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()

    def generate(self, extra: str = "") -> str:
        timestamp = str(int(time.time()))
        payload = f"{timestamp}:{extra}"
        signature = self._sign(payload)
        raw = f"{payload}:{signature}"
        return base64.urlsafe_b64encode(raw.encode()).decode()

    def verify(self, state: str, *, max_age: int = 600) -> Option[str]:
        try:
            raw = base64.urlsafe_b64decode(state.encode()).decode()
        except (binascii.Error, UnicodeDecodeError):
            return Option(None)

        parts = raw.split(":", 2)
        if len(parts) != _EXPECTED_PARTS:
            return Option(None)

        timestamp_str, extra, signature = parts

        try:
            timestamp = int(timestamp_str)
        except ValueError:
            return Option(None)

        if time.time() - timestamp > max_age:
            return Option(None)

        expected = self._sign(f"{timestamp_str}:{extra}")
        if not hmac.compare_digest(signature, expected):
            return Option(None)

        return Option(extra)
