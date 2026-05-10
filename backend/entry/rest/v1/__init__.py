from litestar import Router, get

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


def create_v1_router() -> Router:
    return Router(
        path="/v1",
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
