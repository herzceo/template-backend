from uuid import UUID

from litestar import Controller, delete, get, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import sessions
from backend.internal.di import Depends


class SessionsController(Controller):
    path = "/sessions"
    tags = ("Sessions",)

    @get("/")
    async def list_sessions(
        self,
        handler: Depends[sessions.ListSessionsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Session]:
        return await handler(sessions.ListSessionsCommand(offset=offset, limit=limit))

    @post("/")
    async def create_session(
        self,
        data: sessions.CreateSessionCommand,
        handler: Depends[sessions.CreateSessionHandler],
    ) -> dtos.Session:
        return await handler(data)

    @get("/{id:str}")
    async def get_session(
        self,
        id: str,
        handler: Depends[sessions.GetSessionHandler],
    ) -> dtos.Session:
        return await handler(sessions.GetSessionCommand(id=UUID(id)))

    @delete("/{id:str}")
    async def delete_session(
        self,
        id: str,
        handler: Depends[sessions.DeleteSessionHandler],
    ) -> None:
        return await handler(sessions.DeleteSessionCommand(id=UUID(id)))
