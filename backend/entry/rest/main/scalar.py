from typing import Any, final

from litestar import Request
from litestar.openapi.plugins import ScalarRenderPlugin


@final
class RelativeScalarRenderPlugin(ScalarRenderPlugin):
    """Scalar docs that load the spec via a path relative to the docs page.

    Litestar's ``route_reverse`` builds an app-root-absolute URL
    (``/docs/openapi.json``) that ignores any reverse-proxy mount prefix. When
    the API is served behind a stripped prefix (e.g. ``/api`` → backend), the
    docs page at ``/api/docs`` would then fetch ``/docs/openapi.json`` and 404.

    The spec is always served as a child of the docs path (``{docs}/openapi.json``),
    so a link relative to the current page resolves correctly under any prefix
    without depending on the ASGI ``root_path`` being forwarded.
    """

    @staticmethod
    def get_openapi_json_route(request: Request[Any, Any, Any]) -> str:
        basename = request.scope["path"].rsplit("/", 1)[-1]
        return f"{basename}/openapi.json" if basename else "openapi.json"
