from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
from sqlalchemy.types import Boolean


@declarative_mixin
class WithActive:
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
