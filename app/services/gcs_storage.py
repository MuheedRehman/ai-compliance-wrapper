"""GCS-backed artifact storage.

Enabled by setting the GCS_BUCKET environment variable.
Falls back to no-op when the variable is absent, so database storage is used.
"""
import os
from datetime import timedelta

_BUCKET_NAME = os.environ.get("GCS_BUCKET", "")


def is_configured() -> bool:
    return bool(_BUCKET_NAME)


def _client():
    from google.cloud import storage  # type: ignore[import]
    return storage.Client()


def upload(storage_key: str, content: bytes, content_type: str) -> None:
    client = _client()
    bucket = client.bucket(_BUCKET_NAME)
    blob = bucket.blob(storage_key)
    blob.upload_from_string(content, content_type=content_type)


def download(storage_key: str) -> bytes:
    client = _client()
    bucket = client.bucket(_BUCKET_NAME)
    blob = bucket.blob(storage_key)
    return blob.download_as_bytes()


def signed_url(storage_key: str, expiry_seconds: int = 3600) -> str | None:
    """Generate a V4 signed download URL valid for *expiry_seconds*.

    Returns None if signing is not available (e.g. no service-account credentials
    in the environment), so callers can fall back to the proxy download endpoint.
    """
    try:
        client = _client()
        bucket = client.bucket(_BUCKET_NAME)
        blob = bucket.blob(storage_key)
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiry_seconds),
            method="GET",
        )
    except Exception:
        return None
