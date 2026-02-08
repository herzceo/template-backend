from abc import abstractmethod
from typing import Protocol

from backend.domain.repos.commiter import Commiter

from .user import UserRepo


class RepoGateway(Protocol):
    @property
    @abstractmethod
    def user(self) -> UserRepo: ...

    @property
    @abstractmethod
    def commiter(self) -> Commiter: ...
