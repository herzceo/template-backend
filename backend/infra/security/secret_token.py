import hashlib
import secrets
from typing import final


@final
class ImplSHA256SecretTokenGenerator:
    def generate(self) -> str:
        return secrets.token_urlsafe(32)

    def hash(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
