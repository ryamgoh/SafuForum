# Moderation text worker (toxicornotclassifier)

Consumes moderation text jobs from RabbitMQ and publishes moderation results.

## Architecture
- `app/events/rabbitmq.py`: persistent RabbitMQ event loop (consume + publish)
- `app/events/service.py`: event handler (JSON -> domain -> result event)
- `app/inference/service.py`: inference service (text -> decision)
- `app/inference/pipeline.py`: model loading + vectorization (text -> proba pipeline)

## AMQP topology
- Ingress exchange (topic): `x.moderation.ingress`
- Queue: `q.moderation.job.text.toxicornotclassifier`
- Binding key: `moderation.job.text`
- Result exchange (direct): `x.moderation.result`
- Result queue: `q.moderation.job.result`
- Routing key: `moderation.job.result`

## Environment variables
- `RABBITMQ_HOST` (default: `rabbitmq`)
- `RABBITMQ_PORT` (default: `5672`)
- `RABBITMQ_USERNAME` / `RABBITMQ_PASSWORD` (default: `guest`/`guest`)
- `RABBITMQ_VHOST` (default: `/`)
- `AMQP_URL` (optional; overrides the host/port/user/pass fields). For the default vhost (`/`), use `/%2F` (example: `amqp://guest:guest@rabbitmq:5672/%2F`), not a bare trailing slash.
- `MODEL_ARTIFACTS_PATH` (default: `/model/toxic_logreg.joblib`)
- `W2V_MODEL_PATH` (optional; e.g. `word2vec_200.kv`)
- `W2V_FORMAT` (default: `vectors`; `vectors|full`)
- `W2V_STEM` (default: `false`)
- `TOXIC_THRESHOLD` (default: `0.5`)
- `RESULT_QUEUE_NAME` (default: `q.moderation.job.result`)

Result messages preserve the incoming `correlationId`; `messageId` is a random UUIDv4.

This worker expects the classifier `toxic_logreg.joblib` plus the Word2Vec embeddings to be present at runtime (commonly mounted from `ai/toxicornot_textclassifier/results/`, which is gitignored).
If `W2V_MODEL_PATH` is not set, it is inferred by scanning the `MODEL_ARTIFACTS_PATH` directory for a single `*.kv` (vectors) or `*.model` (full) file.
If `W2V_MODEL_PATH` is relative, it is resolved relative to `MODEL_ARTIFACTS_PATH`'s directory.

Embeddings can be either:
- Word2Vec full model (`W2V_FORMAT=full`): deploy the `.model` file plus its companion `.npy` files (including `*.syn1neg.npy`).
- KeyedVectors only (`W2V_FORMAT=vectors`): deploy the vectors file (often `.kv`) plus its companion `*.vectors.npy` file; no `syn1neg` needed.

## Run
- `uv run python -m app`
