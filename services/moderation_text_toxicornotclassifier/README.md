# Moderation text worker (toxicornotclassifier)

Consumes moderation text jobs from RabbitMQ and publishes moderation results.

## Architecture
- `app/events/rabbitmq.py`: persistent RabbitMQ event loop (consume + publish)
- `app/events/service.py`: event handler (JSON -> domain -> result event)
- `app/inference/service.py`: inference service (text -> decision)
- `app/inference/toxicornot_model.py`: model loading + vectorization

## AMQP topology
- Ingress exchange (topic): `x.moderation.ingress`
- Queue: `q.moderation.job.text.toxicornotclassifier`
- Binding key: `moderation.job.text`
- Result exchange (direct): `x.moderation.result`
- Routing key: `moderation.job.result`

## Environment variables
- `RABBITMQ_HOST` (default: `rabbitmq`)
- `RABBITMQ_PORT` (default: `5672`)
- `RABBITMQ_USERNAME` / `RABBITMQ_PASSWORD` (default: `guest`/`guest`)
- `RABBITMQ_VHOST` (default: `/`)
- `AMQP_URL` (optional; overrides the host/port/user/pass fields)
- `MODEL_ARTIFACTS_PATH` (default: `/model/toxic_logreg.joblib`)
- `TOXIC_THRESHOLD` (default: `0.5`)

Result messages preserve the incoming `correlationId`; `messageId` is a UUID (UUIDv5 by default, derived from `SERVICE_NAME` + `correlationId`).

This worker expects the `toxic_logreg.joblib` + Word2Vec `.model` artifacts to be present at runtime (commonly mounted from `ai/toxicornot_textclassifier/results/`, which is gitignored).

## Run
- `uv run python -m app`
