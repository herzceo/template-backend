from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from backend.app.shared.db.database import Database
from backend.domain.entities.notification import Notification
from backend.domain.enums import NotificationAudience

if TYPE_CHECKING:
    from dishka import AsyncContainer


async def create_notification(
    container: AsyncContainer,
    tenant_id: UUID,
    *,
    title: str = "Test Notification",
    body: str = "Test body",
    audience: NotificationAudience = NotificationAudience.ALL,
    urgency: int = 20,
) -> Notification:
    async with container() as c:
        db: Database = await c.get(Database)
        async with db:
            notification = Notification(
                id=uuid4(),
                tenant_id=tenant_id,
                title=title,
                body=body,
                audience=audience,
                urgency=urgency,
            )
            created = (await db.gateway.notification.create(notification)).some(
                RuntimeError("Failed to create notification")
            )
            await db.commit()
    return created
