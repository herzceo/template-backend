from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

from backend.internal.case import pascal_case_to_snake_case


class Base(DeclarativeBase):
    __abstract__: bool = True

    @declared_attr.directive
    def __tablename__(self) -> str:
        return pascal_case_to_snake_case(self.__name__)
