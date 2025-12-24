import logging
import time
import uuid
import pika
from typing import Any, Optional
from app.domain import JobCompletedEvent
from app.settings import Settings
from app.events.service import EventService

LOGGER = logging.getLogger(__name__)

class RabbitMQEventLoop:
    """Event loop for consuming and publishing messages via RabbitMQ."""
    def __init__(self, settings: Settings, event_service: EventService):
        self._settings = settings
        self._service = event_service
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._publish_returned: bool = False
        self._publish_return_reason: str | None = None

    def _setup_topology(self):
        """Standardizes exchanges and bindings."""
        # Incoming: Where sub-services send results
        self._channel.exchange_declare(self._settings.result_exchange, "direct", durable=True)
        self._channel.queue_declare(self._settings.result_queue_name, durable=True)
        self._channel.queue_bind(
            self._settings.result_queue_name,
            self._settings.result_exchange,
            self._settings.result_routing_key
        )

        # Outgoing: Where the final result goes
        self._channel.exchange_declare(self._settings.egress_exchange, "topic", durable=True)

        self._channel.basic_qos(prefetch_count=self._settings.prefetch_count)
        self._channel.confirm_delivery()
        self._channel.add_on_return_callback(self._on_return)

    def _on_return(self, _ch, method, properties, _body):
        self._publish_returned = True
        cid = getattr(properties, "correlation_id", None)
        self._publish_return_reason = f"{getattr(method, 'reply_code', '?')}:{getattr(method, 'reply_text', '?')}; correlation_id={cid}"
        LOGGER.error("Egress publish was returned (unroutable): %s", self._publish_return_reason)

    @staticmethod
    def _coerce_header_value(value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8")
            except Exception:
                value = value.decode("utf-8", errors="replace")
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _get_header(headers: dict[Any, Any], key: str) -> object | None:
        if key in headers:
            return headers[key]
        encoded_key = key.encode("utf-8")
        if encoded_key in headers:
            return headers[encoded_key]
        return None

    def _on_message(self, ch, method, props, body):
        cid = None
        if props is not None and props.correlation_id:
            cid = self._coerce_header_value(props.correlation_id)

        headers: dict[Any, Any] = {}
        if props is not None and props.headers:
            headers = props.headers
        service_name = self._coerce_header_value(self._get_header(headers, "x-service-name"))

        try:
            # Handle the logic via service
            final_event = self._service.handle_message(body, cid, service_name=service_name)

            # Only publish if the aggregator has determined the job is fully complete
            if final_event:
                if not cid:
                    raise RuntimeError("final_event returned without correlation_id")
                self._publish_final(final_event, cid)
                try:
                    self._service.cleanup(cid)
                except Exception:
                    # Cleanup failures should not block publishing; state will expire via TTL.
                    LOGGER.exception("Failed cleaning up aggregation state; correlation_id=%s", cid)
                LOGGER.info("Published final aggregated result for CID: %s", cid)

            # Ack only after any required final publish has succeeded.
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            LOGGER.error("Error processing message: %s", e)
            # Requeue to retry: aggregation state is still present in Redis.
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _publish_final(self, event: JobCompletedEvent, cid: str | None):
        self._publish_returned = False
        self._publish_return_reason = None
        properties = pika.BasicProperties(
            correlation_id=cid,
            message_id=str(uuid.uuid4()),
            content_type="application/json",
            delivery_mode=2, # Persistent
            priority=0,
            headers={
                "x-service-name": self._settings.service_name,
            },
        )
        published = self._channel.basic_publish(
            exchange=self._settings.egress_exchange,
            routing_key=self._settings.egress_routing_key,
            body=event.model_dump_json(by_alias=True, exclude_none=True),
            properties=properties,
            mandatory=True,
        )
        if self._connection is not None:
            self._connection.process_data_events(time_limit=0)
        if published is False:
            raise RuntimeError("Broker did not confirm the final publish (nack).")
        if self._publish_returned:
            raise RuntimeError(f"Final publish was unroutable: {self._publish_return_reason}")

    def run_forever(self) -> int:
        """Main event loop to connect, consume, and process messages."""
        while True:
            try:
                # Force the virtual host to '/' if it's missing or empty
                params = pika.URLParameters(str(self._settings.amqp_url))

                # Defensive check: if vhost is empty or just whitespace, default to '/'
                if not params.virtual_host or params.virtual_host.strip() == "":
                    params.virtual_host = "/"

                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()

                self._setup_topology()

                self._channel.basic_consume(
                    queue=self._settings.result_queue_name,
                    on_message_callback=self._on_message
                )

                LOGGER.info("Aggregator started. Waiting for result events...")
                self._channel.start_consuming()

            except pika.exceptions.ConnectionClosedByBroker:
                break
            except pika.exceptions.AMQPChannelError as err:
                LOGGER.error("Channel error: %s", err)
                break
            except (pika.exceptions.AMQPConnectionError, Exception) as err:
                LOGGER.warning("Connection lost, retrying in %s seconds: %s", 
                               self._settings.reconnect_delay_seconds, err)
                time.sleep(self._settings.reconnect_delay_seconds)
                continue
            
        return 0
