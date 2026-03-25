from backend.internal.dto import StructDTO


class PaginatedResponse[T: StructDTO](StructDTO):
    items: list[T]
    total: int
    offset: int
    limit: int
