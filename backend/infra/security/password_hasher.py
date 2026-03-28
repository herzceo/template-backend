from typing import final

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


@final
class ImplArgon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hash: str) -> bool:
        try:
            return self._hasher.verify(hash, password)
        except VerifyMismatchError:
            return False
