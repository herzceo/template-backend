import mimetypes
from typing import final
from uuid import UUID

from backend.app.shared.errors import NotFoundError, ValidationFailedError
from backend.app.shared.ports.storage import ConfirmedUpload, PendingUpload
from backend.infra.database.object import blurhash, keys
from backend.infra.external.s3.client import S3Client
from backend.infra.external.s3.config import S3Config
from backend.infra.external.s3.errors import ObjectNotFoundError
from backend.infra.external.s3.io import ObjectMeta

_TEMP_PREFIX_SEGMENTS = 4


@final
class S3ObjectStore:
    __slots__ = ("_client", "_config")

    def __init__(self, client: S3Client, config: S3Config) -> None:
        self._client = client
        self._config = config

    async def request_upload(self, *, user_id: UUID, original_filename: str) -> PendingUpload:
        key = keys.temp_upload_key(user_id, original_filename)
        result = await self._client.presigned_url(key, method="put_object")
        return PendingUpload(url=result.url, key=key, expires_in=result.expires_in)

    async def confirm_upload(
        self,
        *,
        pending_key: str,
        user_id: UUID,
        tenant_id: UUID,
        original_filename: str,
    ) -> ConfirmedUpload:
        self._validate_filename(original_filename)
        self._validate_key_ownership(pending_key, user_id)

        meta = await self._head_or_raise(pending_key)
        self._validate_size(meta.size)

        final_key = keys.permanent_asset_key(tenant_id, original_filename)
        await self._client.copy(pending_key, final_key)
        await self._client.delete(pending_key)

        guessed, _ = mimetypes.guess_type(original_filename)
        content_type = guessed or meta.content_type or "application/octet-stream"
        hash_ = await self._try_compute_blurhash(final_key, content_type)

        return ConfirmedUpload(
            key=final_key,
            size=meta.size,
            content_type=content_type,
            blurhash=hash_,
        )

    async def _try_compute_blurhash(self, key: str, content_type: str) -> str | None:
        if not blurhash.is_image(content_type):
            return None
        data = await self._client.download(key)
        return blurhash.compute(data)

    async def _head_or_raise(self, key: str) -> ObjectMeta:
        try:
            return await self._client.head(key)
        except ObjectNotFoundError:
            raise NotFoundError(
                message="Uploaded file not found at the provided key",
                details={"key": key},
            ) from None

    def _validate_filename(self, filename: str) -> None:
        if not filename or "\0" in filename or ".." in filename or "/" in filename:
            raise ValidationFailedError(
                message="Invalid filename",
                details={"original_filename": filename},
            )

    def _validate_key_ownership(self, pending_key: str, user_id: UUID) -> None:
        parts = pending_key.split("/")
        if (
            len(parts) < _TEMP_PREFIX_SEGMENTS
            or parts[0] != "temp"
            or parts[1] != "uploads"
            or parts[3] != str(user_id)
        ):
            raise ValidationFailedError(
                message="Temp key does not belong to the authenticated user",
                details={"key": pending_key},
            )

    def _validate_size(self, size: int) -> None:
        max_size = self._config.S3_UPLOAD_MAX_SIZE_BYTES
        if size > max_size:
            raise ValidationFailedError(
                message=f"File size {size} exceeds maximum {max_size}",
                details={"size": size, "max": max_size},
            )
