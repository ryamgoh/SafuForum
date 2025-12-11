"""Configuration loader for TextModerationService (template)."""
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings for TextModerationService."""
    # Security
    secret_key: str = Field(
        "a-string-secret-at-least-256-bits-long",
        alias="SECRET_KEY"
    )
    algorithm: str = Field("HS256", alias="ALGORITHM")
    access_token_expires_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRES_MINUTES")
    refresh_token_expires_minutes: int = Field(24 * 60, alias="REFRESH_TOKEN_EXPIRES_MINUTES")
    refresh_token_rotation: bool = Field(True, alias="REFRESH_TOKEN_ROTATION")

    # Database
    postgres_host: str = Field("0.0.0.0", alias="POSTGRES_HOST")
    postgres_port: str = Field("5432", alias="POSTGRES_PORT")
    postgres_user: str = Field("user", alias="POSTGRES_USER")
    postgres_password: str = Field("user", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("user", alias="POSTGRES_DB")

    # Messaging & S3
    # rabbitmq_url: str = Field(..., alias="RABBITMQ_URL")
    # text_request_queue: str = Field("q.text.moderation", alias="TEXT_REQUEST_QUEUE")
    # text_completed_exchange: str = \
    #     Field("ex.analysis.text.completed", alias="TEXT_COMPLETED_EXCHANGE")
    # s3_endpoint: str | None = Field(None, alias="S3_ENDPOINT")
    # s3_bucket: str | None = Field(None, alias="S3_BUCKET")
    # s3_access_key: str | None = Field(None, alias="S3_ACCESS_KEY")
    # s3_secret_key: str | None = Field(None, alias="S3_SECRET_KEY")
    # composite_timeout_seconds: float = Field(2.0, alias="COMPOSITE_TIMEOUT_SECONDS")
    # detector_mode: str = Field("in-process", alias="DETECTOR_MODE")

def get_settings() -> Settings:
    """Returns the application settings."""
    return Settings()
