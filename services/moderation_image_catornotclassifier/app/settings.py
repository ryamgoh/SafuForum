"""Application settings for the cat-or-not moderation worker."""

from pydantic import AmqpDsn, Field, TypeAdapter, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Explicitly cast the string to the expected type
AMQP_DEFAULT = TypeAdapter(AmqpDsn).validate_python(
    "amqp://guest:guest@rabbitmq:5672/%2F"
)

class Settings(BaseSettings):
    """Application settings for the cat-or-not moderation worker."""

    # Use Case-Insensitive environment variable lookup
    model_config = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False
    )

    # Use AmqpDsn for automatic URL validation (user, pass, host, port)
    amqp_url: AmqpDsn = Field(default=AMQP_DEFAULT, alias="AMQP_URL")

    # S3 storage
    s3_url: str = Field(default="http://seaweed-s3:8333", alias="S3_URL")
    s3_access_key_id: str = Field(default="dev", alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field(default="dev", alias="S3_SECRET_ACCESS_KEY")
    
    # If set, only these buckets are allowed. Defaults to just `image_bucket`.
    allowed_buckets: list[str] = Field(default_factory=list, alias="ALLOWED_BUCKETS")
    image_bucket: str = Field(default="safu-forum-images", alias="IMAGE_BUCKET")

    # inference
    model_path: str = Field(default="/model/model.pth", alias="MODEL_PATH")
    torch_device: str = Field(default="cpu", alias="TORCH_DEVICE")
    cat_threshold: float = Field(default=0.5, alias="CAT_THRESHOLD")
    not_cat_threshold: float = Field(default=0.5, alias="NOT_CAT_THRESHOLD")

    # Safety limits
    max_image_bytes: int = Field(default=10_000_000, alias="MAX_IMAGE_BYTES")
    max_image_pixels: int = Field(default=40_000_000, alias="MAX_IMAGE_PIXELS")


    # Ingress Exchange Configuration
    ingress_exchange_name: str = Field(default="x.moderation.ingress", alias="INGRESS_EXCHANGE_NAME")
    ingress_binding_key: str = Field(default="moderation.job.image")
    ingress_queue_name: str = Field(default="q.moderation.job.image.catornotclassifier")

    # Result Exchange Configuration
    result_exchange_name: str = Field(default="x.moderation.result", alias="RESULT_EXCHANGE_NAME")
    result_routing_key: str = Field(default="moderation.job.result")

    service_name: str = Field(default="catornotclassifier")
    log_level: str = Field(default="INFO")

    @field_validator("allowed_buckets", mode="before")
    @classmethod
    def _parse_allowed_buckets(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            # Accept comma-separated env vars (e.g. "bucket-a,bucket-b").
            return [part.strip() for part in stripped.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def _validate_thresholds_and_limits(self):
        if not (0.0 <= self.not_cat_threshold <= self.cat_threshold <= 1.0):
            raise ValueError(
                "Invalid thresholds: require 0 <= NOT_CAT_THRESHOLD <= CAT_THRESHOLD <= 1"
            )
        if self.max_image_bytes <= 0:
            raise ValueError("MAX_IMAGE_BYTES must be > 0")
        if self.max_image_pixels <= 0:
            raise ValueError("MAX_IMAGE_PIXELS must be > 0")
        return self

# Usage
settings = Settings()
