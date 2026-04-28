from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from backend.infra.external.s3 import io
from backend.infra.external.s3.errors import (
    BucketNotFoundError,
    CopyError,
    DownloadError,
    ObjectNotFoundError,
    S3Error,
    UploadError,
)

if TYPE_CHECKING:
    from aiobotocore.client import AioBaseClient

    from backend.infra.external.s3.config import S3Config


class S3Client:
    __slots__ = ("_client", "_config")

    def __init__(self, config: S3Config, client: AioBaseClient) -> None:  # type: ignore[no-any-unimported]
        self._config = config
        self._client = client

    def _bucket(self, bucket: str | None) -> str:
        return bucket or self._config.S3_BUCKET

    async def upload(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        bucket: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> io.UploadResult:
        target_bucket = self._bucket(bucket)
        kwargs: dict[str, Any] = {
            "Bucket": target_bucket,
            "Key": key,
            "Body": data,
            "ContentType": content_type,
        }
        if metadata:
            kwargs["Metadata"] = metadata

        try:
            response = await self._client.put_object(**kwargs)
        except self._client.exceptions.NoSuchBucket as e:
            raise BucketNotFoundError(
                message=f"Bucket not found: {target_bucket}",
                details={"bucket": target_bucket},
            ) from e
        except Exception as e:
            raise UploadError(
                message=f"Upload failed for {key}: {e}",
                details={"key": key, "bucket": target_bucket},
            ) from e

        return io.UploadResult(
            key=key,
            bucket=target_bucket,
            etag=response.get("ETag", "").strip('"'),
            version_id=response.get("VersionId"),
        )

    async def download(
        self,
        key: str,
        *,
        bucket: str | None = None,
    ) -> bytes:
        target_bucket = self._bucket(bucket)
        try:
            response = await self._client.get_object(Bucket=target_bucket, Key=key)
            return await response["Body"].read()  # type: ignore[no-any-return]
        except self._client.exceptions.NoSuchKey as e:
            raise ObjectNotFoundError(
                message=f"Object not found: {key}",
                details={"key": key, "bucket": target_bucket},
            ) from e
        except self._client.exceptions.NoSuchBucket as e:
            raise BucketNotFoundError(
                message=f"Bucket not found: {target_bucket}",
                details={"bucket": target_bucket},
            ) from e
        except Exception as e:
            raise DownloadError(
                message=f"Download failed for {key}: {e}",
                details={"key": key, "bucket": target_bucket},
            ) from e

    async def presigned_url(
        self,
        key: str,
        *,
        bucket: str | None = None,
        expires_in: int | None = None,
        method: Literal["get_object", "put_object"] = "get_object",
    ) -> io.PresignedUrlResult:
        target_bucket = self._bucket(bucket)
        expiry = expires_in or self._config.S3_PRESIGNED_URL_EXPIRY
        try:
            url = await self._client.generate_presigned_url(
                method,
                Params={"Bucket": target_bucket, "Key": key},
                ExpiresIn=expiry,
            )
        except Exception as e:
            raise S3Error(
                message=f"Failed to generate presigned URL for {key}: {e}",
                details={"key": key, "bucket": target_bucket},
            ) from e

        return io.PresignedUrlResult(url=url, key=key, expires_in=expiry)

    async def delete(
        self,
        key: str,
        *,
        bucket: str | None = None,
    ) -> None:
        target_bucket = self._bucket(bucket)
        try:
            await self._client.delete_object(Bucket=target_bucket, Key=key)
        except self._client.exceptions.NoSuchBucket as e:
            raise BucketNotFoundError(
                message=f"Bucket not found: {target_bucket}",
                details={"bucket": target_bucket},
            ) from e
        except Exception as e:
            raise S3Error(
                message=f"Delete failed for {key}: {e}",
                details={"key": key, "bucket": target_bucket},
            ) from e

    async def exists(
        self,
        key: str,
        *,
        bucket: str | None = None,
    ) -> bool:
        target_bucket = self._bucket(bucket)
        try:
            await self._client.head_object(Bucket=target_bucket, Key=key)
        except self._client.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise S3Error(
                message=f"Failed to check existence of {key}: {e}",
                details={"key": key, "bucket": target_bucket},
            ) from e
        return True

    async def head(
        self,
        key: str,
        *,
        bucket: str | None = None,
    ) -> io.ObjectMeta:
        target_bucket = self._bucket(bucket)
        try:
            response = await self._client.head_object(Bucket=target_bucket, Key=key)
        except self._client.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                raise ObjectNotFoundError(
                    message=f"Object not found: {key}",
                    details={"key": key, "bucket": target_bucket},
                ) from e
            raise S3Error(
                message=f"Head failed for {key}: {e}",
                details={"key": key, "bucket": target_bucket},
            ) from e

        return io.ObjectMeta(
            key=key,
            size=response.get("ContentLength", 0),
            content_type=response.get("ContentType", ""),
            last_modified=str(response.get("LastModified", "")),
            etag=response.get("ETag", "").strip('"'),
        )

    async def copy(
        self,
        source_key: str,
        destination_key: str,
        *,
        source_bucket: str | None = None,
        destination_bucket: str | None = None,
    ) -> io.CopyResult:
        src_bucket = self._bucket(source_bucket)
        dst_bucket = self._bucket(destination_bucket)
        try:
            response = await self._client.copy_object(
                Bucket=dst_bucket,
                Key=destination_key,
                CopySource={"Bucket": src_bucket, "Key": source_key},
            )
        except self._client.exceptions.NoSuchBucket as e:
            raise BucketNotFoundError(
                message=f"Bucket not found: {dst_bucket}",
                details={"bucket": dst_bucket},
            ) from e
        except self._client.exceptions.NoSuchKey as e:
            raise ObjectNotFoundError(
                message=f"Source object not found: {source_key}",
                details={"key": source_key, "bucket": src_bucket},
            ) from e
        except Exception as e:
            raise CopyError(
                message=f"Copy failed from {source_key} to {destination_key}: {e}",
                details={
                    "source_key": source_key,
                    "destination_key": destination_key,
                    "source_bucket": src_bucket,
                    "destination_bucket": dst_bucket,
                },
            ) from e

        etag = response.get("CopyObjectResult", {}).get("ETag", "").strip('"')
        return io.CopyResult(
            source_key=source_key,
            destination_key=destination_key,
            bucket=dst_bucket,
            etag=etag,
        )
