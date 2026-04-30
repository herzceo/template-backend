from uuid import UUID

from backend.internal.dto import StructDTO


class Permission(StructDTO):
    id: UUID
    codename: str
    description: str | None
