from typing import Any

from backend.internal.dto import StructDTO


class UpdateUserBody(StructDTO):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None


class UpdateTenantBody(StructDTO):
    name: str | None = None
    slug: str | None = None
    settings: dict[str, Any] | None = None
    owner_id: str | None = None


class UpdateRoleBody(StructDTO):
    name: str | None = None
    description: str | None = None


class UpdatePermissionBody(StructDTO):
    codename: str | None = None
    description: str | None = None


class UpdateAssetBody(StructDTO):
    blurhash: str | None = None
    original_filename: str | None = None


class UpdateNotificationBody(StructDTO):
    title: str | None = None
    body: str | None = None
    urgency: int | None = None
