from typing import final
from uuid import UUID

from backend.app.shared.ports.storage import ConfirmedUpload, PendingUpload


@final
class NullObjectStore:
    async def request_upload(self, *, user_id: UUID, original_filename: str) -> PendingUpload:
        msg = "Object storage is not configured"
        raise NotImplementedError(msg)

    async def confirm_upload(
        self,
        *,
        pending_key: str,
        user_id: UUID,
        tenant_id: UUID,
        original_filename: str,
    ) -> ConfirmedUpload:
        msg = "Object storage is not configured"
        raise NotImplementedError(msg)
