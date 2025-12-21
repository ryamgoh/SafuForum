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

JAVA_TYPE_ID = "com.SafuForumBackend.moderation.event.ModerationJobCompletedEvent"


def setup_topology(channel: pika.adapters.blocking_connection.BlockingChannel, settings: Settings) -> None:
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
    channel.queue_declare(queue=settings.queue_name, durable=True)
    channel.queue_bind(
        queue=settings.queue_name,
        exchange=settings.ingress_exchange,
        routing_key=settings.ingress_routing_key,
    )
    channel.basic_qos(prefetch_count=settings.prefetch_count)


def _build_message_id(settings: Settings, *, correlation_id: str | None) -> str:
    if correlation_id:
        return str(uuid.uuid5(settings.message_id_namespace, f"{settings.service_name}:{correlation_id}"))
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
        delivery_mode=2,
        correlation_id=correlation_id,
        message_id=message_id,
        headers={
            "__TypeId__": JAVA_TYPE_ID,
            "x-service-name": settings.service_name,
        },
    )

    body = json.dumps(completion.model_dump(by_alias=True), ensure_ascii=False).encode("utf-8")
    channel.basic_publish(
        exchange=settings.result_exchange,
        routing_key=settings.result_routing_key,
        body=body,
        properties=props,
        mandatory=True,
    )


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
        params = pika.URLParameters(self._settings.amqp_url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        setup_topology(channel, self._settings)
        channel.confirm_delivery()

        def on_message(
            ch: pika.adapters.blocking_connection.BlockingChannel,
            method: pika.spec.Basic.Deliver,
            properties: pika.BasicProperties,
            body: bytes,
        ) -> None:
            incoming_correlation_id = None
            if properties is not None and properties.correlation_id:
                incoming_correlation_id = str(properties.correlation_id)

            try:
                processed = self._event_service.handle_message(
                    body=body,
                    correlation_id=incoming_correlation_id,
                )
            except Exception as exc:
                LOGGER.exception("Failed processing inbound event: %s", exc)
                processed = ProcessedEvent(
                    completion=ModerationJobCompletedEvent(
                        moderation_job_id=None,
                        post_id=None,
                        post_version=None,
                        status="failed",
                        reason=str(exc),
                    ),
                    correlation_id=incoming_correlation_id,
                )

            try:
                _publish_result(
                    ch,
                    self._settings,
                    completion=processed.completion,
                    correlation_id=processed.correlation_id,
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as exc:
                LOGGER.exception("Failed publishing moderation completion: %s", exc)
                try:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                except Exception:
                    pass

        channel.basic_consume(queue=self._settings.queue_name, on_message_callback=on_message, auto_ack=False)
        LOGGER.info(
            "Listening on queue=%s exchange=%s key=%s; publishing exchange=%s key=%s",
            self._settings.queue_name,
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
