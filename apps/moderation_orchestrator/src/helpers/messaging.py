"""RabbitMQ wiring helpers (placeholder).

Fill in channel/connection setup with aio-pika. Signatures are kept small so
the orchestrator can publish fan-out requests and completions.
"""
import uuid
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict

EVENT_TYPE_TASK_REQUESTED = "Moderation.Task.Requested.v1"
EVENT_TYPE_TASK_COMPLETED = "Moderation.Task.Completed.v1"
EVENT_TYPE_JOB_COMPLETED = "Moderation.Job.Completed.v1"


def _envelope(event_type: str, correlation_id: str, service_id: str, payload: Dict) -> Dict:
    """Create a standard event envelope."""
    return {
        "message_id": str(uuid.uuid4()),
        "type": event_type,
        "correlation_id": correlation_id,
        "service_id": service_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }


async def start_consumer(queue_name: str, handler: Callable[[Dict], Awaitable[None]]):
    """Start consuming from `queue_name` and dispatch to handler.

    TODO: implement aio-pika connection, declare queues/exchanges, and
    deserialize messages into dict payloads before handing to `handler`.
    """
    raise NotImplementedError


async def publish_task_request(
    correlation_id: str,
    service_id: str,
    payload: Dict,
):
    """Publish a moderation request to a service (text or image).

    TODO: serialize and publish to the modality-specific exchange/routing key.
    """
    envelope = _envelope(
        EVENT_TYPE_TASK_REQUESTED,
        correlation_id=correlation_id,
        service_id="orchestrator",
        payload={
            "job_id": correlation_id,
            "task": {"service_id": service_id},
            "content": payload.get("content", {}),
        },
    )
    raise NotImplementedError(envelope)


async def publish_completed(original_event: Dict, decision: Dict):
    """Publish `Moderation.Content.Completed` (or equivalent) back to content service.

    TODO: serialize and publish to the configured exchange/routing key.
    """
    envelope = _envelope(
        EVENT_TYPE_JOB_COMPLETED,
        correlation_id=decision["job_id"],
        service_id="orchestrator",
        payload={
            "job_id": decision["job_id"],
            "final_verdict": decision["verdict"],
            "final_score": decision.get("score"),
            "timed_out": decision.get("timed_out", False),
            "task_count": decision.get("task_count"),
            "responses": decision.get("responses"),
        },
    )
    raise NotImplementedError(envelope)
