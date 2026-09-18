import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from cloudbox_api.core.config import settings

minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def ensure_bucket_exists() -> None:
    if not minio_client.bucket_exists(settings.MINIO_BUCKET):
        minio_client.make_bucket(settings.MINIO_BUCKET)


def generate_storage_key(owner_id: uuid.UUID, file_id: uuid.UUID) -> str:
    return f"users/{owner_id}/{file_id}"


def generate_upload_url(storage_key: str, content_type: str) -> str:
    return minio_client.presigned_put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=storage_key,
        expires=timedelta(seconds=settings.MINIO_UPLOAD_URL_EXPIRY_SECONDS),
    )


def generate_download_url(storage_key: str) -> str:
    return minio_client.presigned_get_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=storage_key,
        expires=timedelta(seconds=settings.MINIO_DOWNLOAD_URL_EXPIRY_SECONDS),
    )


def object_exists(storage_key: str) -> bool:
    try:
        minio_client.stat_object(settings.MINIO_BUCKET, storage_key)
        return True
    except S3Error:
        return False


def get_object_size(storage_key: str) -> int:
    stat = minio_client.stat_object(settings.MINIO_BUCKET, storage_key)
    return stat.size


def delete_object(storage_key: str) -> None:
    try:
        minio_client.remove_object(settings.MINIO_BUCKET, storage_key)
    except S3Error:
        pass
