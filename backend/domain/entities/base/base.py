from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

from backend.internal.case import pascal_case_to_snake_case


class Base(DeclarativeBase):
    __abstract__: bool = True

    if TYPE_CHECKING:
        id: Any

    @declared_attr.directive
    def __tablename__(self) -> str:
        return pascal_case_to_snake_case(self.__name__)

    def to_builtins(self) -> dict[str, Any]:
        d = {}
        for column in self.__table__.columns:
            d[column.name] = getattr(self, column.name)
        return d
