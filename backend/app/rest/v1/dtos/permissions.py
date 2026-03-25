from backend.internal.dto import StructDTO


class Permission(StructDTO):
    id: str
    codename: str
    description: str | None
