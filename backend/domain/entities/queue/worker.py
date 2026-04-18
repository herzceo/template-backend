from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import BigInteger, Integer, String

from backend.domain.entities.base import Base


class Worker(Base):
    __tablename__ = "queue_worker"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    queues: Mapped[list[str]] = mapped_column(ARRAY(String(128)), nullable=False)
    concurrency: Mapped[int] = mapped_column(Integer, nullable=False)
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
