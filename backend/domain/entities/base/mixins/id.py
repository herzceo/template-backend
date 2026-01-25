from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
from sqlalchemy.types import UUID as SQL_UUID
from sqlalchemy.types import Integer
from uuid_utils import uuid4
from uuid_utils.compat import UUID


@declarative_mixin
class WithIntegerID:
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )


@declarative_mixin
class WithUUIDID:
    id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
