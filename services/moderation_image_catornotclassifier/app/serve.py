from typing import Annotated
import io

from faststream import Context, FastStream
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
    RabbitResponse,
)

from app.settings import settings
from app.s3_handler import S3Handler
from app.inference import ImagePredictor
from app.types import IngressMessageBody, ResultMessageBody, ModerationStatus
from PIL import Image


broker = RabbitBroker(str(settings.amqp_url))

app = FastStream()
app.set_broker(broker)

s3_handler = S3Handler()
img_predictor = ImagePredictor(model_path=settings.model_path)

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
    
    payload = data.payload.strip().lstrip("/")
    bucket, key = payload.split("/", 1)  # bucket="safu-forum-images", key="uploads/uuid.jpg"

    if bucket != settings.image_bucket:
        raise ValueError(f"Invalid bucket: {bucket}")

    # Download the image bytes from S3
    image_bytes = await s3_handler.download_bytes(
       bucket=bucket,
       key=key 
    )
    
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    prediction = img_predictor.predict(image)
    
    if prediction == 1:
        # Image is classified as "cat"
        processed_body: ResultMessageBody = ResultMessageBody(
            status=ModerationStatus.REJECTED, reason="CAT detected"
        )
    else:       
        # Image is classified as "not cat"
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
