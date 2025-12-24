"""Application settings for the Moderation Aggregator Service."""
from pydantic import Field, AmqpDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings for the Moderation Aggregator Service."""
    # Use Case-Insensitive environment variable lookup
    model_config = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False
    )

    # Use AmqpDsn for automatic URL validation (user, pass, host, port)
    amqp_url: AmqpDsn = Field(alias="AMQP_URL")

    # Result Exchange Configuration
    result_exchange: str = "x.moderation.result"
    result_routing_key: str = "moderation.job.result"
    result_queue_name: str = "q.moderation.job.result"

    # Egress Exchange Configuration
    egress_exchange: str = "x.moderation.egress"
    egress_routing_key: str = "moderation.job.completed"

    service_name: str = "moderation_aggregator"
    prefetch_count: int = Field(default=1, ge=1)
    reconnect_delay_seconds: float = Field(default=5.0, ge=0.0)
    log_level: str = "INFO"

    docker_host: str = Field(default="tcp://docker-socket-proxy:2375", alias="DOCKER_HOST")
    redis_host: str = Field(default="redis", alias="REDIS_HOST")

    # Ensure Docker labels are consistent
    moderation_label: str = Field(default="domain=moderation", alias="MODERATION_LABEL")

# Usage
settings = Settings()
