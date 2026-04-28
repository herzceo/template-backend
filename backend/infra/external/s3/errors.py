from __future__ import annotations

from backend.infra.external.errors import ExternalError


class S3Error(ExternalError):
    message = "S3 error"
    code = "s3_error"


class ObjectNotFoundError(S3Error):
    message = "Object not found"
    code = "s3_object_not_found"


class BucketNotFoundError(S3Error):
    message = "Bucket not found"
    code = "s3_bucket_not_found"


class UploadError(S3Error):
    message = "Upload failed"
    code = "s3_upload_error"


class DownloadError(S3Error):
    message = "Download failed"
    code = "s3_download_error"


class CopyError(S3Error):
    message = "Copy failed"
    code = "s3_copy_error"
