from typing import Any

from litestar import MediaType, Response
from msgspec import field

from backend.internal.dto import StructDTO


class ErrorDetail(StructDTO):
    code: int
    message: str
    status: str
    details: list[dict[str, Any]] = field(default_factory=list)


async def wrap_ok(response: Response[Any]) -> Response[Any]:
    if response.status_code == 204:  # noqa: PLR2004
        return response
    return Response(
        {"type": "ok", "data": response.content},
        status_code=response.status_code,
        media_type=MediaType.JSON,
    )
