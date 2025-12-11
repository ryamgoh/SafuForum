"""RabbitMQ wiring helpers (placeholder).

Fill in channel/connection setup with aio-pika. The signatures are kept
small so `app.py` can call `start_consumer` and `publish_completed`.
"""
from typing import Awaitable, Callable, Dict


async def start_consumer(queue_name: str, handler: Callable[[Dict], Awaitable[None]]):
    """Start consuming from `queue_name` and dispatch to handler.

    TODO: implement aio-pika connection, declare queues/exchanges, and
    deserialize messages into dict payloads before handing to `handler`.
    """
    raise NotImplementedError


async def publish_completed(event: Dict, decision: Dict):
    """Publish `Moderation.ModerationOrchestratorService.AnalysisCompleted.v1`.

    TODO: serialize and publish to the configured exchange/routing key.
    """
    raise NotImplementedError
