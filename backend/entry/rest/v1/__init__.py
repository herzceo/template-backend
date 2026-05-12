from dishka.integrations.litestar import DishkaRouter
from litestar import get

from backend.entry.rest.common.response import wrap_ok

from .assets import AssetsController
from .audit_logs import AuditLogsController
from .auth import AuthController
from .notifications import NotificationsController
from .permissions import PermissionsController
from .profile import ProfileController
from .roles import RolesController
from .sessions import SessionsController
from .tenants import TenantsController
from .users import UsersController


@get("/health", exclude_from_auth=True, tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


def create_v1_router() -> DishkaRouter:
    return DishkaRouter(
        path="/v1",
        after_request=wrap_ok,
        route_handlers=[
            health,
            AuthController,
            UsersController,
            TenantsController,
            RolesController,
            PermissionsController,
            SessionsController,
            AssetsController,
            NotificationsController,
            AuditLogsController,
            ProfileController,
        ],
    )
