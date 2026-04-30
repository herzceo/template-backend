from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from aiobotocore.session import get_session
from minio import Minio
from testcontainers.minio import MinioContainer

from backend.infra.database.object import S3ObjectStore
from backend.infra.external.s3.client import S3Client
from backend.infra.external.s3.config import S3Config

_BUCKET = "test-assets"
_ACCESS_KEY = "minioadmin"
_SECRET_KEY = "minioadmin"


@pytest.fixture(scope="session")
def minio_endpoint() -> Iterator[str]:
    with MinioContainer() as minio:
        host = minio.get_container_host_ip()
        port = minio.get_exposed_port(9000)
        endpoint = f"http://{host}:{port}"
        Minio(
            f"{host}:{port}",
            access_key=_ACCESS_KEY,
            secret_key=_SECRET_KEY,
            secure=False,
        ).make_bucket(_BUCKET)
        yield endpoint


@pytest.fixture
def s3_config(minio_endpoint: str) -> S3Config:
    return S3Config(
        S3_ACCESS_KEY_ID=_ACCESS_KEY,
        S3_SECRET_ACCESS_KEY=_SECRET_KEY,
        S3_ENDPOINT_URL=minio_endpoint,
        S3_BUCKET=_BUCKET,
    )


@pytest.fixture
async def s3_client(s3_config: S3Config) -> AsyncIterator[S3Client]:
    session = get_session()
    async with session.create_client(
        "s3",
        region_name=s3_config.S3_REGION,
        aws_access_key_id=s3_config.S3_ACCESS_KEY_ID,
        aws_secret_access_key=s3_config.S3_SECRET_ACCESS_KEY,
        endpoint_url=s3_config.S3_ENDPOINT_URL,
    ) as raw_client:
        yield S3Client(config=s3_config, client=raw_client)


@pytest.fixture
def object_store(s3_client: S3Client, s3_config: S3Config) -> S3ObjectStore:
    return S3ObjectStore(client=s3_client, config=s3_config)
