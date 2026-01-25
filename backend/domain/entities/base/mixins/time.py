from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, column_property, declarative_mixin, declared_attr, mapped_column


@declarative_mixin
class WithTime:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        onupdate=func.now(),
        server_default=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @declared_attr
    @classmethod
    def is_deleted(cls) -> Mapped[bool]:
        return column_property(cls.deleted_at.isnot(None))
