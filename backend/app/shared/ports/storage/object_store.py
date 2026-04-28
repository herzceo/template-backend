from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.internal.dto import StructDTO


class PendingUpload(StructDTO):
    url: str
    key: str
    expires_in: int


class ConfirmedUpload(StructDTO):
    key: str
    size: int
    content_type: str
    blurhash: str | None = None


class ObjectStore(Protocol):
    @abstractmethod
    async def request_upload(self, *, user_id: UUID, original_filename: str) -> PendingUpload: ...

    @abstractmethod
    async def confirm_upload(
        self,
        *,
        pending_key: str,
        user_id: UUID,
        tenant_id: UUID,
        original_filename: str,
    ) -> ConfirmedUpload: ...
