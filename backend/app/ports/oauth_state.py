from abc import abstractmethod
from typing import Protocol

from backend.internal import Option


class OAuthStateSigner(Protocol):
    @abstractmethod
    def generate(self, extra: str = "") -> str: ...

    @abstractmethod
    def verify(self, state: str, *, max_age: int = 600) -> Option[str]: ...
