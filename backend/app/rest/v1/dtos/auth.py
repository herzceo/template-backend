from backend.internal.dto import StructDTO


class AuthContext[T](StructDTO):
    token: str
    data: T
