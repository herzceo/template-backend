from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import BigInteger, Boolean, Integer, String

from backend.domain.entities.base import Base


class Job(Base):
    __tablename__ = "queue_job"
    __table_args__ = (
        Index(
            "ix_queue_job_fetch",
            "priority",
            "id",
            postgresql_where=text("status = 'todo'"),
        ),
        Index(
            "ix_queue_job_queueing_lock",
            "queueing_lock",
            unique=True,
            postgresql_where=text("status = 'todo'"),
        ),
        Index(
            "ix_queue_job_execution_lock",
            "execution_lock",
            unique=True,
            postgresql_where=text("status = 'doing'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    queue_name: Mapped[str] = mapped_column(
        String(128), nullable=False, default="default", index=True
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    execution_lock: Mapped[str | None] = mapped_column(String(128), nullable=True)
    queueing_lock: Mapped[str | None] = mapped_column(String(128), nullable=True)
    args: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="todo", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    abort_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    worker_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
