"""S3-compatible object storage."""

from app.core.configuration import Settings
from app.core.exceptions import ServiceValidationError


class S3FileStorage:
    """Persist uploads to an S3-compatible bucket."""

    def __init__(self, settings: Settings) -> None:
        if not settings.s3_bucket:
            raise ServiceValidationError(
                "S3_BUCKET is required when STORAGE_BACKEND=s3"
            )
        self._settings = settings
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import boto3
        except ImportError as exc:
            raise ServiceValidationError(
                "boto3 is required for S3 storage backend"
            ) from exc

        client_kwargs: dict[str, str] = {}
        if self._settings.aws_region:
            client_kwargs["region_name"] = self._settings.aws_region
        if self._settings.aws_endpoint_url:
            client_kwargs["endpoint_url"] = self._settings.aws_endpoint_url

        self._client = boto3.client("s3", **client_kwargs)
        return self._client

    def put(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self._get_client().put_object(
            Bucket=self._settings.s3_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    def get(self, key: str) -> bytes:
        response = self._get_client().get_object(
            Bucket=self._settings.s3_bucket,
            Key=key,
        )
        return response["Body"].read()

    def delete(self, key: str) -> None:
        self._get_client().delete_object(
            Bucket=self._settings.s3_bucket,
            Key=key,
        )

    def exists(self, key: str) -> bool:
        try:
            from botocore.exceptions import ClientError

            self._get_client().head_object(
                Bucket=self._settings.s3_bucket,
                Key=key,
            )
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise
