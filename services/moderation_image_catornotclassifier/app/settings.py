"""Application settings for the Moderation Aggregator Service."""
from pydantic import AmqpDsn, Field, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict


# Explicitly cast the string to the expected type
AMQP_DEFAULT = TypeAdapter(AmqpDsn).validate_python("amqp://guest:guest@rabbitmq:5672/%2F")
class Settings(BaseSettings):
    """Application settings for the Moderation Aggregator Service."""
    # Use Case-Insensitive environment variable lookup
    model_config = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False
    )

    # Use AmqpDsn for automatic URL validation (user, pass, host, port)
    amqp_url: AmqpDsn = Field(default=AMQP_DEFAULT, alias="AMQP_URL")

    # Ingress Exchange Configuration
    ingress_exchange_name: str = Field(default="x.moderation.ingress", alias="INGRESS_EXCHANGE_NAME")
    ingress_binding_key: str = Field(default="moderation.job.image")
    ingress_queue_name: str = Field(default="q.moderation.job.image.catornotclassifier")

    # Result Exchange Configuration
    result_exchange_name: str = Field(default="x.moderation.result", alias="RESULT_EXCHANGE_NAME")
    result_routing_key: str = Field(default="moderation.job.result")

    service_name: str = Field(default="catornotclassifier")
    log_level: str = Field(default="INFO")


# Usage
settings = Settings()
