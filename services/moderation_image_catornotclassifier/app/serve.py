from typing import Annotated, Any
import io
import asyncio
import logging

from faststream import Context, FastStream
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
    RabbitResponse,
)

from app.settings import settings
from app.s3_handler import PayloadParseError, S3Handler, parse_s3_locator
from app.inference import ImagePredictor, ModelLoadError
from app.types import IngressMessageBody, ResultMessageBody, ModerationStatus
from PIL import Image, UnidentifiedImageError
from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError


logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

Image.MAX_IMAGE_PIXELS = settings.max_image_pixels

broker = RabbitBroker(str(settings.amqp_url))

app = FastStream()
app.set_broker(broker)

s3_handler = S3Handler()
img_predictor = ImagePredictor(
    model_path=settings.model_path,
    device=settings.torch_device,
    cat_threshold=settings.cat_threshold,
    not_cat_threshold=settings.not_cat_threshold,
)

CorrelationId = Annotated[str | None, Context("message.correlation_id")]

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

def _decode_image_bytes(image_bytes: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(image_bytes))
    image.load()
    return image.convert("RGB")


@broker.subscriber(queue=ingress_queue, exchange=ingress_exchange)
@broker.publisher(exchange=result_exchange, routing_key=settings.result_routing_key)
async def base_handler(
    data: IngressMessageBody, cor_id: CorrelationId
) -> RabbitResponse:
    headers: dict[str, Any] = {
        "x-service-name": settings.service_name,
        "x-moderation-type": "image",
    }

    try:
        bucket, key = parse_s3_locator(data.payload)
    except PayloadParseError as exc:
        logger.warning(
            "Moderation FAILED (bad payload) cid=%s payload=%r error=%s",
            cor_id,
            data.payload[:200],
            str(exc),
        )
        return RabbitResponse(
            ResultMessageBody(status=ModerationStatus.FAILED, reason=str(exc)),
            headers=headers,
            correlation_id=cor_id,
        )

    allowed_buckets = set(settings.allowed_buckets or [settings.image_bucket])
    if bucket not in allowed_buckets:
        logger.warning(
            "Moderation FAILED (bucket not allowed) cid=%s bucket=%s key=%s",
            cor_id,
            bucket,
            key,
        )
        return RabbitResponse(
            ResultMessageBody(
                status=ModerationStatus.FAILED,
                reason=f"Bucket not allowed: {bucket}",
            ),
            headers=headers,
            correlation_id=cor_id,
        )

    # Download the image bytes from S3
    try:
        image_bytes = await s3_handler.download_bytes(
            bucket=bucket,
            key=key,
            max_bytes=settings.max_image_bytes,
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "ClientError")
        logger.warning(
            "Moderation FAILED (s3 error) cid=%s bucket=%s key=%s code=%s",
            cor_id,
            bucket,
            key,
            code,
        )
        return RabbitResponse(
            ResultMessageBody(
                status=ModerationStatus.FAILED,
                reason=f"S3 error ({code}) for {bucket}/{key}",
            ),
            headers=headers,
            correlation_id=cor_id,
        )
    except (EndpointConnectionError, ReadTimeoutError):
        logger.exception(
            "Transient S3 error cid=%s downloading %s/%s", cor_id, bucket, key
        )
        raise
    except ValueError as exc:
        logger.warning(
            "Moderation FAILED (s3) cid=%s bucket=%s key=%s error=%s",
            cor_id,
            bucket,
            key,
            str(exc),
        )
        return RabbitResponse(
            ResultMessageBody(status=ModerationStatus.FAILED, reason=str(exc)),
            headers=headers,
            correlation_id=cor_id,
        )

    # Decode image with basic safety limits.
    try:
        image = await asyncio.to_thread(_decode_image_bytes, image_bytes)
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning(
            "Moderation FAILED (invalid image) cid=%s bucket=%s key=%s error=%s",
            cor_id,
            bucket,
            key,
            type(exc).__name__,
        )
        return RabbitResponse(
            ResultMessageBody(
                status=ModerationStatus.FAILED,
                reason=f"Invalid image: {type(exc).__name__}",
            ),
            headers=headers,
            correlation_id=cor_id,
        )
    except Image.DecompressionBombError:
        logger.warning(
            "Moderation FAILED (decompression bomb) cid=%s bucket=%s key=%s",
            cor_id,
            bucket,
            key,
        )
        return RabbitResponse(
            ResultMessageBody(
                status=ModerationStatus.FAILED,
                reason="Image rejected: decompression bomb detected",
            ),
            headers=headers,
            correlation_id=cor_id,
        )

    try:
        prediction = await asyncio.to_thread(img_predictor.predict, image)
    except (FileNotFoundError, ModelLoadError) as exc:
        logger.exception(
            "Model load/inference failure cid=%s bucket=%s key=%s",
            cor_id,
            bucket,
            key,
        )
        return RabbitResponse(
            ResultMessageBody(status=ModerationStatus.FAILED, reason=str(exc)[:200]),
            headers=headers,
            correlation_id=cor_id,
        )
    except Exception as exc:
        logger.exception(
            "Unhandled inference error cid=%s bucket=%s key=%s",
            cor_id,
            bucket,
            key,
        )
        return RabbitResponse(
            ResultMessageBody(
                status=ModerationStatus.FAILED,
                reason=f"Inference error: {type(exc).__name__}",
            ),
            headers=headers,
            correlation_id=cor_id,
        )

    if prediction.label == "cat":
        processed_body = ResultMessageBody(
            status=ModerationStatus.REJECTED,
            reason=f"CAT detected (p={prediction.probability:.4f})",
        )
    elif prediction.label == "not_cat":
        processed_body = ResultMessageBody(
            status=ModerationStatus.APPROVED,
            reason=f"No cat detected (p={prediction.probability:.4f})",
        )
    else:
        processed_body = ResultMessageBody(
            status=ModerationStatus.FAILED,
            reason=f"Uncertain classification (p={prediction.probability:.4f})",
        )

    logger.log(
        logging.INFO
        if processed_body.status != ModerationStatus.FAILED
        else logging.WARNING,
        "Moderation result cid=%s bucket=%s key=%s status=%s reason=%s",
        cor_id,
        bucket,
        key,
        processed_body.status.value,
        processed_body.reason,
    )
        
    # Return a RabbitResponse to set headers and correlation_id declaratively
    return RabbitResponse(
        processed_body,
        headers=headers,
        correlation_id=cor_id,
    )
