from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import BigInteger, String

from backend.domain.entities.base import Base


class WorkerEvent(Base):
    __tablename__ = "queue_worker_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("queue_worker.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
