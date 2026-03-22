from functools import cached_property
from typing import final

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.repos import RepoGateway

from .commiter import ImplCommiter
from .user import ImplUserRepo


@final
class ImplRepoGateway(RepoGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @cached_property
    def user(self) -> ImplUserRepo:
        return ImplUserRepo(self._session)

    @cached_property
    def commiter(self) -> ImplCommiter:
        return ImplCommiter(self._session)
