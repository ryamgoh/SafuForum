import asyncio
import boto3
from botocore.config import Config
from app.settings import settings


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


    def _download_bytes(self, bucket: str, key: str) -> bytes:
        resp = self.s3.get_object(Bucket=bucket, Key=key)
        body = resp["Body"]
        try:
            return body.read()
        finally:
            body.close()


    async def download_bytes(self, bucket: str, key: str) -> bytes:
        return await asyncio.to_thread(self._download_bytes, bucket, key)