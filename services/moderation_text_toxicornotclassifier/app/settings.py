from __future__ import annotations

import os
import uuid
from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    amqp_url: str
    ingress_exchange: str
    ingress_exchange_type: str
    ingress_routing_key: str
    ingress_queue_name: str
    result_exchange: str
    result_exchange_type: str
    result_routing_key: str
    result_queue_name: str
    message_id_namespace: uuid.UUID
    service_name: str
    toxic_threshold: float = Field(ge=0.0, le=1.0)
    model_artifacts_path: str
    w2v_model_path: str = Field(min_length=1)
    w2v_format: str
    w2v_stem: bool
    prefetch_count: int = Field(ge=1)
    reconnect_delay_seconds: float = Field(ge=0.0)
    log_level: str


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _infer_w2v_model_path(*, artifacts_path: str, w2v_format: str) -> str:
    artifacts = Path(artifacts_path)
    search_dir = artifacts if artifacts.is_dir() else artifacts.parent

    fmt = str(w2v_format or "").strip().lower()
    if fmt in {"vectors", "kv", "keyedvectors"}:
        patterns = ("*.kv",)
    elif fmt in {"full", "model", "word2vec"}:
        patterns = ("*.model",)
    else:
        patterns = ("*.kv", "*.model")

    candidates = sorted({p for pattern in patterns for p in search_dir.glob(pattern) if p.is_file()})
    if len(candidates) == 1:
        return str(candidates[0])

    patterns_str = ", ".join(patterns)
    if not candidates:
        raise ValueError(
            "W2V_MODEL_PATH is required (or an embeddings file must be present next to MODEL_ARTIFACTS_PATH). "
            f"Looked for {patterns_str} in {search_dir}. "
            "Set W2V_MODEL_PATH to the embeddings file (e.g. 'word2vec_200.kv') and restart."
        )

    found = ", ".join(str(p.name) for p in candidates)
    raise ValueError(
        "W2V_MODEL_PATH is required and multiple embeddings files were found. "
        f"Found in {search_dir}: {found}. "
        "Set W2V_MODEL_PATH to choose one and restart."
    )


def load_settings() -> Settings:
    host = _env("RABBITMQ_HOST", "rabbitmq")
    port = _env("RABBITMQ_PORT", "5672")
    user = _env("RABBITMQ_USERNAME", "guest")
    password = _env("RABBITMQ_PASSWORD", "guest")
    vhost = _env("RABBITMQ_VHOST", "/")
    vhost_encoded = quote(vhost, safe="")
    amqp_url = _env("AMQP_URL", f"amqp://{user}:{password}@{host}:{port}/{vhost_encoded}")

    model_artifacts_path = _env("MODEL_ARTIFACTS_PATH", "/model/toxic_logreg.joblib")
    w2v_format = _env("W2V_FORMAT", "vectors")
    w2v_model_path = _env_optional("W2V_MODEL_PATH") or _infer_w2v_model_path(
        artifacts_path=model_artifacts_path,
        w2v_format=w2v_format,
    )

    return Settings.model_validate(
        {
            "amqp_url": amqp_url,
            "ingress_exchange": _env("INGRESS_EXCHANGE", "x.moderation.ingress"),
            "ingress_exchange_type": _env("INGRESS_EXCHANGE_TYPE", "topic"),
            "ingress_routing_key": _env("INGRESS_ROUTING_KEY", "moderation.job.text"),
            "ingress_queue_name": _env("INGRESS_QUEUE_NAME", "q.moderation.job.text.toxicornotclassifier"),
            "result_exchange": _env("RESULT_EXCHANGE", "x.moderation.result"),
            "result_exchange_type": _env("RESULT_EXCHANGE_TYPE", "direct"),
            "result_routing_key": _env("RESULT_ROUTING_KEY", "moderation.job.result"),
            "result_queue_name": _env("RESULT_QUEUE_NAME", "q.moderation.job.result"),
            "message_id_namespace": _env("MESSAGE_ID_NAMESPACE", str(uuid.NAMESPACE_URL)),
            "service_name": _env("SERVICE_NAME", "toxicornotclassifier"),
            "toxic_threshold": _env("TOXIC_THRESHOLD", "0.5"),
            "model_artifacts_path": model_artifacts_path,
            "w2v_model_path": w2v_model_path,
            "w2v_format": w2v_format,
            "w2v_stem": _env("W2V_STEM", "false"),
            "prefetch_count": _env("PREFETCH_COUNT", "1"),
            "reconnect_delay_seconds": _env("RECONNECT_DELAY_SECONDS", "5"),
            "log_level": _env("LOG_LEVEL", "INFO"),
        }
    )
