from abc import abstractmethod
from typing import Protocol

from .user import UserQueryService


class QueryServiceGateway(Protocol):
    @property
    @abstractmethod
    def user(self) -> UserQueryService: ...
