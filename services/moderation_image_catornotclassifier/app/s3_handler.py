import asyncio
from urllib.parse import unquote, urlparse

import boto3
from botocore.config import Config
from app.settings import settings


class PayloadParseError(ValueError):
    pass


def parse_s3_locator(payload: str) -> tuple[str, str]:
    raw = payload.strip()
    if not raw:
        raise PayloadParseError("Empty payload")

    if raw.startswith(("http://", "https://", "s3://")):
        parsed = urlparse(raw)
        if raw.startswith("s3://"):
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
        else:
            path = unquote(parsed.path).lstrip("/")
            if "/" not in path:
                raise PayloadParseError("Expected URL path in the form /bucket/key")
            bucket, key = path.split("/", 1)
    else:
        path = unquote(raw.lstrip("/"))
        if "/" not in path:
            raise PayloadParseError("Expected payload in the form bucket/key")
        bucket, key = path.split("/", 1)

    bucket = bucket.strip()
    key = key.strip().lstrip("/")
    if not bucket or not key:
        raise PayloadParseError("Invalid bucket/key")

    return bucket, key


class S3Handler:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name="us-east-1",
            config=Config(s3={"addressing_style": "path"}),
        )


    def _download_bytes(self, bucket: str, key: str, *, max_bytes: int | None) -> bytes:
        resp = self.s3.get_object(Bucket=bucket, Key=key)
        content_length = resp.get("ContentLength")
        if (
            max_bytes is not None
            and isinstance(content_length, int)
            and content_length > max_bytes
        ):
            raise ValueError(
                f"S3 object too large ({content_length} bytes > {max_bytes} bytes)"
            )

        body = resp["Body"]
        try:
            if max_bytes is None:
                return body.read()
            data = body.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError(f"S3 object too large (> {max_bytes} bytes)")
            return data
        finally:
            body.close()


    async def download_bytes(
        self, bucket: str, key: str, *, max_bytes: int | None = None
    ) -> bytes:
        return await asyncio.to_thread(
            self._download_bytes, bucket, key, max_bytes=max_bytes
        )
