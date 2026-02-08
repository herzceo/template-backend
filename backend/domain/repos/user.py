from typing import Protocol

from backend.domain.entities import User
from backend.domain.repos.base import CRUDSupported


class UserRepo(CRUDSupported[User], Protocol): ...
