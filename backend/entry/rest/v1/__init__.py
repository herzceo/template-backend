from litestar import Router

from .assets import AssetsController
from .audit_logs import AuditLogsController
from .auth import AuthController
from .notifications import NotificationsController
from .permissions import PermissionsController
from .roles import RolesController
from .sessions import SessionsController
from .tenants import TenantsController
from .users import UsersController


def create_v1_router() -> Router:
    return Router(
        path="/v1",
        route_handlers=[
            AuthController,
            UsersController,
            TenantsController,
            RolesController,
            PermissionsController,
            SessionsController,
            AssetsController,
            NotificationsController,
            AuditLogsController,
        ],
    )
