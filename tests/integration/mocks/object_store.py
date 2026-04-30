from __future__ import annotations

from dataclasses import dataclass, field
from typing import final
from uuid import UUID, uuid4

from backend.app.shared.ports.storage.object_store import (
    ConfirmedUpload,
    PendingUpload,
)


@final
@dataclass
class MockObjectStore:
    _confirmed_keys: list[str] = field(default_factory=list)

    async def request_upload(self, *, user_id: UUID, original_filename: str) -> PendingUpload:
        key = f"tmp/{user_id}/{uuid4()}/{original_filename}"
        return PendingUpload(url=f"https://mock-s3/upload/{key}", key=key, expires_in=3600)

    async def confirm_upload(
        self,
        *,
        pending_key: str,
        user_id: UUID,
        tenant_id: UUID,
        original_filename: str,  # noqa: ARG002
    ) -> ConfirmedUpload:
        _ = pending_key
        final_key = f"assets/{tenant_id}/{user_id}/{uuid4()}"
        self._confirmed_keys.append(final_key)
        return ConfirmedUpload(
            key=final_key,
            size=1024,
            content_type="image/jpeg",
            blurhash="LGF5]+Yk^6#M@-5c,1J5@[or[Q6.",
        )

    def get_confirmed_keys(self) -> list[str]:
        return list(self._confirmed_keys)
