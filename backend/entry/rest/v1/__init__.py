from litestar import Router

from .users import UsersController


def create_v1_router() -> Router:
    return Router(
        path="/v1",
        route_handlers=[
            UsersController,
        ],
    )
