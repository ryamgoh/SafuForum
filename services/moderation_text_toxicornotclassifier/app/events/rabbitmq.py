from __future__ import annotations

import json
import logging
import time
import uuid

import pika

from app.domain import ModerationJobCompletedEvent
from app.events.service import ModerationEventService, ProcessedEvent
from app.settings import Settings


LOGGER = logging.getLogger("app")

def setup_topology(channel: pika.adapters.blocking_connection.BlockingChannel, settings: Settings) -> None:
    """Set up exchanges, queues, and bindings."""
    channel.exchange_declare(
        exchange=settings.ingress_exchange,
        exchange_type=settings.ingress_exchange_type,
        durable=True,
    )
    channel.exchange_declare(
        exchange=settings.result_exchange,
        exchange_type=settings.result_exchange_type,
        durable=True,
    )

    # Declare and bind the queue for outgoing moderation results
    channel.queue_declare(queue=settings.result_queue_name, durable=True)
    channel.queue_bind(
        queue=settings.result_queue_name,
        exchange=settings.result_exchange,
        routing_key=settings.result_routing_key,
    )
    
    # Declare and bind the queue for incoming moderation jobs
    channel.queue_declare(queue=settings.ingress_queue_name, durable=True)
    channel.queue_bind(
        queue=settings.ingress_queue_name,
        exchange=settings.ingress_exchange,
        routing_key=settings.ingress_routing_key,
    )
    
    # Set up QoS
    channel.basic_qos(prefetch_count=settings.prefetch_count)


def _build_message_id(settings: Settings, *, correlation_id: str | None) -> str:
    """Generate a message ID (correlation_id carries job identity)."""
    return str(uuid.uuid4())


def _publish_result(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    settings: Settings,
    *,
    completion: ModerationJobCompletedEvent,
    correlation_id: str | None,
) -> None:
    message_id = _build_message_id(settings, correlation_id=correlation_id)
    props = pika.BasicProperties(
        content_type="application/json",
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
        correlation_id=correlation_id,
        message_id=message_id,
        priority=0,
        headers={
            "x-service-name": settings.service_name,
        },
    )

    body = json.dumps(completion.model_dump(by_alias=True), ensure_ascii=False).encode("utf-8")
    published = channel.basic_publish(
        exchange=settings.result_exchange,
        routing_key=settings.result_routing_key,
        body=body,
        properties=props,
        mandatory=True,
    )
    if published is False:
        raise RuntimeError("Broker did not confirm the moderation completion publish (nack).")


class RabbitMQEventLoop:
    """
    RabbitMQ-based event loop for moderation events.
    """
    def __init__(self, settings: Settings, event_service: ModerationEventService) -> None:
        self._settings = settings
        self._event_service = event_service

    def run_forever(self) -> int:
        """
        Run the event loop, reconnecting on failure.
        """
        while True:
            try:
                self._run_once()
                return 0
            except KeyboardInterrupt:
                return 0
            except Exception as exc:
                LOGGER.exception("Service crashed; retrying: %s", exc)
                time.sleep(self._settings.reconnect_delay_seconds)

    def _run_once(self) -> None:
        """
        Run the event loop once.
        """
        params = pika.URLParameters(self._settings.amqp_url)
        # Pika expects the default vhost (`/`) to be encoded as `%2F` in the URL.
        # If the URL ends with a bare slash (e.g. `amqp://host/`), `virtual_host` becomes empty.
        # Default to `/` to avoid hard-to-debug 530 NOT_ALLOWED errors.
        if not params.virtual_host or params.virtual_host.strip() == "":
            params.virtual_host = "/"
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        setup_topology(channel, self._settings)
        
        # We want this publisher to also use publisher confirms
        # to ensure our messages are delivered
        channel.confirm_delivery()

        # Start consuming messages
        channel.basic_consume(queue=self._settings.ingress_queue_name, on_message_callback=self._on_message_callback, auto_ack=False)
        LOGGER.info(
            "Listening on queue=%s exchange=%s key=%s; publishing exchange=%s key=%s",
            self._settings.ingress_queue_name,
            self._settings.ingress_exchange,
            self._settings.ingress_routing_key,
            self._settings.result_exchange,
            self._settings.result_routing_key,
        )
        try:
            channel.start_consuming()
        finally:
            try:
                channel.close()
            finally:
                connection.close()

    def _on_message_callback(
        self,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """
        Callback for incoming messages.
        Process the message and publish the result.
        """
        incoming_correlation_id = None
        if properties is not None and properties.correlation_id:
            raw_correlation_id = properties.correlation_id
            if isinstance(raw_correlation_id, bytes):
                try:
                    raw_correlation_id = raw_correlation_id.decode("utf-8")
                except Exception:
                    raw_correlation_id = raw_correlation_id.decode("utf-8", errors="replace")
            normalized = str(raw_correlation_id).strip()
            incoming_correlation_id = normalized or None

        try:
            processed = self._event_service.handle_message(
                body=body,
                correlation_id=incoming_correlation_id,
            )
            LOGGER.info(
                "Processed moderation job; correlation_id=%s status=%s reason=%s",
                processed.correlation_id,
                processed.completion.status,
                processed.completion.reason,
            )
        except Exception as exc:
            LOGGER.exception("Failed processing inbound event: %s", exc)
            processed = ProcessedEvent(
                completion=ModerationJobCompletedEvent(
                    status="failed",
                    reason=str(exc),
                ),
                correlation_id=incoming_correlation_id,
            )

        try:
            _publish_result(
                channel,
                self._settings,
                completion=processed.completion,
                correlation_id=processed.correlation_id,
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            LOGGER.exception("Failed publishing moderation completion: %s", exc)
            # Avoid tight redelivery loops when publishing fails; let the outer loop reconnect with backoff.
            raise
