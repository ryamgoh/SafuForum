# Moderation aggregator

Consumes per-worker moderation result events from RabbitMQ and publishes a single aggregated completion event.

## Architecture
- `app/events/rabbitmq.py`: persistent RabbitMQ consumer + publisher
- `app/events/service.py`: aggregation logic (Redis-backed)
- `app/events/docker_registry.py`: tracks active moderation workers via Docker API

## AMQP topology
- Result exchange (direct): `x.moderation.result` (inbound)
- Result queue: `q.moderation.job.result`
- Result routing key: `moderation.job.result`
- Egress exchange (topic): `x.moderation.egress` (outbound)
- Egress routing key: `moderation.job.completed`

## Environment variables
- `AMQP_URL` (required; example: `amqp://guest:guest@rabbitmq:5672/%2F`)
- `DOCKER_HOST` (default: `tcp://docker-socket-proxy:2375`)
- `REDIS_HOST` (default: `redis`)

## Inbound result schema
- Body fields are expected in `camelCase` (e.g. `moderationJobId`, `postId`, `postVersion`, `status`, `reason`).
- The worker name is taken from the `x-service-name` AMQP header (preferred) or the body (`serviceName` / `service_name`).

## Run
- `uv run python -m app`
