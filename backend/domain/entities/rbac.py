from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.types import UUID as SQL_UUID

from .base import Base

user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", SQL_UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True),
    Column("role_id", SQL_UUID(as_uuid=True), ForeignKey("role.id"), primary_key=True),
)

role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", SQL_UUID(as_uuid=True), ForeignKey("role.id"), primary_key=True),
    Column(
        "permission_id",
        SQL_UUID(as_uuid=True),
        ForeignKey("permission.id"),
        primary_key=True,
    ),
)
