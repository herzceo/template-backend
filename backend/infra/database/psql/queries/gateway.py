from functools import cached_property
from typing import final

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .user import ImplUserQueryService


@final
class ImplQueryServiceGateway:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session_maker = session_maker

    @cached_property
    def user(self) -> ImplUserQueryService:
        return ImplUserQueryService(self._session_maker)
