from typing import final

from backend.domain.entities.user import User
from backend.domain.repos.user import UserRepo

from .base import ImplCRUDSupported


@final
class ImplUserRepo(ImplCRUDSupported[User], UserRepo):
    __slots__ = ()
