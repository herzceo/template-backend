from abc import abstractmethod
from typing import Protocol


class SecretTokenGenerator(Protocol):
    @abstractmethod
    def generate(self) -> str: ...

    @abstractmethod
    def hash(self, token: str) -> str: ...
