from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class Settings:
    amqp_url: str
    ingress_exchange: str
    ingress_exchange_type: str
    ingress_routing_key: str
    queue_name: str
    result_exchange: str
    result_exchange_type: str
    result_routing_key: str
    message_id_namespace: uuid.UUID
    service_name: str
    toxic_threshold: float
    model_artifacts_path: str
    prefetch_count: int
    reconnect_delay_seconds: float
    log_level: str


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


def load_settings() -> Settings:
    host = _env("RABBITMQ_HOST", "rabbitmq")
    port = _env("RABBITMQ_PORT", "5672")
    user = _env("RABBITMQ_USERNAME", "guest")
    password = _env("RABBITMQ_PASSWORD", "guest")
    vhost = _env("RABBITMQ_VHOST", "/")
    vhost_encoded = quote(vhost, safe="")
    amqp_url = _env("AMQP_URL", f"amqp://{user}:{password}@{host}:{port}/{vhost_encoded}")

    namespace_raw = _env("MESSAGE_ID_NAMESPACE", str(uuid.NAMESPACE_URL))

    return Settings(
        amqp_url=amqp_url,
        ingress_exchange=_env("INGRESS_EXCHANGE", "x.moderation.ingress"),
        ingress_exchange_type=_env("INGRESS_EXCHANGE_TYPE", "topic"),
        ingress_routing_key=_env("INGRESS_ROUTING_KEY", "moderation.job.text"),
        queue_name=_env("QUEUE_NAME", "q.moderation.job.text.toxicornotclassifier"),
        result_exchange=_env("RESULT_EXCHANGE", "x.moderation.result"),
        result_exchange_type=_env("RESULT_EXCHANGE_TYPE", "direct"),
        result_routing_key=_env("RESULT_ROUTING_KEY", "moderation.job.result"),
        message_id_namespace=uuid.UUID(namespace_raw),
        service_name=_env("SERVICE_NAME", "toxicornotclassifier"),
        toxic_threshold=float(_env("TOXIC_THRESHOLD", "0.5")),
        model_artifacts_path=_env("MODEL_ARTIFACTS_PATH", "/model/toxic_logreg.joblib"),
        prefetch_count=int(_env("PREFETCH_COUNT", "1")),
        reconnect_delay_seconds=float(_env("RECONNECT_DELAY_SECONDS", "5")),
        log_level=_env("LOG_LEVEL", "INFO"),
    )

