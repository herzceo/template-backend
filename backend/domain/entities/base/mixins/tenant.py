from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
from sqlalchemy.types import UUID as SQL_UUID
from uuid_utils.compat import UUID


@declarative_mixin
class WithTenant:
    tenant_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("tenant.id"),
        index=True,
        nullable=False,
    )
