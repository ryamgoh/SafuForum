from typing import Annotated

from faststream import Context, FastStream
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
    RabbitResponse,
)

from app.settings import settings
from app.types import IngressMessageBody, ResultMessageBody, ModerationStatus


broker = RabbitBroker(str(settings.amqp_url))

app = FastStream()
app.set_broker(broker)

CorrelationId = Annotated[str, Context("message.correlation_id")]

# 1. Define the Ingress exchange and bind to our queue
ingress_exchange = RabbitExchange(
    name=settings.ingress_exchange_name,
    type=ExchangeType.TOPIC,
    durable=True,
)

# 2. Define the Ingress queue for us to bind
ingress_queue = RabbitQueue(
    name=settings.ingress_queue_name,
    routing_key=settings.ingress_binding_key,
    durable=True,
)

# 3. Define the Result exchange for publishing results
result_exchange = RabbitExchange(
    name=settings.result_exchange_name,
    type=ExchangeType.DIRECT,
    durable=True,
)


@broker.subscriber(queue=ingress_queue, exchange=ingress_exchange)
@broker.publisher(exchange=result_exchange, routing_key=settings.result_routing_key)
async def base_handler(
    data: IngressMessageBody, cor_id: CorrelationId
) -> RabbitResponse:
    processed_body: ResultMessageBody = ResultMessageBody(
        status=ModerationStatus.APPROVED, reason="Processed successfully"
    )

    # Return a RabbitResponse to set headers and correlation_id declaratively
    return RabbitResponse(
        processed_body,
        headers={
            "x-service-name": settings.service_name,
            "x-moderation-type": "image",
        },
        correlation_id=cor_id,
    )
