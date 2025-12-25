# Next Steps: `moderation_image_catornotclassifier`

Build `services/moderation_image_catornotclassifier` as a RabbitMQ worker using **FastStream** to consume moderation jobs, fetch the image from your **S3/SeaweedFS** (URL/path is in the job `payload`), run the **cat-or-not** PyTorch model mounted at `/app/models`, and publish a per-service moderation result to `x.moderation.result` with the incoming `correlation_id` preserved.

## Requirements
- Consume moderation jobs from RabbitMQ (`x.moderation.ingress` topic).
- Read `payload` from the job request body (backend currently sends JSON `{ "payload": "..." }`).
- Treat `payload` as an S3 object locator (URL or `bucket/key`-style path).
- Download image bytes from S3 (SeaweedFS S3 gateway).
- Load model from `/app/models/model.pth` (host-mounted from `ai/catornot_imageclassifier/outputs/`).
- Run inference and decide `approved|rejected|failed`.
- Publish result to `x.moderation.result` (direct), routing key `moderation.job.result`, with header `x-service-name`.
- Run as a long-lived container via a `Dockerfile`, starting the worker with `faststream run ...` (via `uv`).

## Scope
- In: new FastStream-based worker service, Dockerfile, docker-compose service stanza + volume mount, minimal README/env contract.
- Out: changing backend event contract or aggregator logic (but see “Risks”; you may need to adjust one of them for correctness).

## Suggested files and entry points
- `services/moderation_image_catornotclassifier/pyproject.toml` (deps + entrypoint)
- `services/moderation_image_catornotclassifier/app/__main__.py` (exports `app` for `faststream run app.__main__:app`)
- `services/moderation_image_catornotclassifier/app/settings.py` (env → settings)
- `services/moderation_image_catornotclassifier/app/domain.py` (Pydantic models: job + completion)
- `services/moderation_image_catornotclassifier/app/events/broker.py` (RabbitBroker/FastStream wiring + topology)
- `services/moderation_image_catornotclassifier/app/events/handler.py` (subscriber handler: download → infer → publish)
- `services/moderation_image_catornotclassifier/app/s3.py` (parse locator + download helper)
- `services/moderation_image_catornotclassifier/app/inference/model.py` (CatCNNModel definition + loader)
- `services/moderation_image_catornotclassifier/app/inference/service.py` (preprocess + inference + threshold)
- `services/moderation_image_catornotclassifier/Dockerfile`
- `docker-compose.yml` (root) add the new service + volume mount

## Data model / contracts
- Inbound: JSON object containing at least `payload: str` (extra fields ignored).
- Outbound: JSON object containing at least:
  - `status: "approved" | "rejected" | "failed"`
  - `reason: str`
  - AMQP props/headers:
    - `correlation_id`: copy from inbound message
    - header `x-service-name`: unique service name (used by aggregator)

## Action items
- [ ] 1) Confirm routing/aggregation model before coding:
  - Aggregator currently expects **one result per running moderation service** (it uses Docker container count). If every job must receive results from all services, jobs will hang unless that’s true.
  - Decide one of:
    - A) This image worker ALSO consumes `moderation.job.text` (as requested) and always publishes a result for each message, OR
    - B) Switch this worker to `moderation.job.image`, but update aggregator to expect only relevant services per job, OR
    - C) Backend includes “expected services/count” in headers/payload and aggregator uses that instead of Docker count.
- [ ] 2) Define env contract in `app/settings.py` (keep everything configurable):
  - Rabbit: `AMQP_URL`, `INGRESS_EXCHANGE`, `INGRESS_ROUTING_KEY`, `INGRESS_QUEUE_NAME`
  - Result: `RESULT_EXCHANGE`, `RESULT_ROUTING_KEY`, `RESULT_QUEUE_NAME`
  - Service: `SERVICE_NAME`, `PREFETCH_COUNT`, `LOG_LEVEL`
  - S3: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION`, `S3_FORCE_PATH_STYLE`, optional `S3_DEFAULT_BUCKET`
  - Model: `MODEL_PATH=/app/models/model.pth`, `CAT_THRESHOLD=0.5`
- [ ] 3) Update `pyproject.toml` deps (via `uv`):
  - Messaging: `faststream[rabbit]`
  - Modeling: `torch`, `torchvision`, `pillow` (and `numpy` if needed)
  - S3: `boto3` (simple) or `aioboto3` (async-native)
  - (Optional) `pydantic` pinned if you want explicit control
- [ ] 4) Implement robust “S3 locator” parsing for `payload`:
  - Accept common forms:
    - `s3://bucket/key`
    - `http(s)://host:port/bucket/key` (Seaweed S3 gateway-style)
    - `bucket/key` (backend currently stores `bucketName + "/" + s3Key`)
    - (Optional) bare `key` using `S3_DEFAULT_BUCKET`
  - Validate/normalize:
    - strip whitespace, drop leading `/`, URL-decode path
    - reject empty bucket/key
    - (Optional security) allowlist bucket(s) / endpoint host to avoid arbitrary fetch/SSRF
- [ ] 5) Implement S3 download helper:
  - Build client with Seaweed-compatible options:
    - endpoint override (e.g. `http://seaweed-s3:8333`)
    - path-style addressing
    - credentials (from env)
  - Download into memory bytes; enforce size limits if you want safety.
- [ ] 6) Port the model architecture from `ai/catornot_imageclassifier/catclassifiercnn.ipynb`:
  - Define `CatCNNModel` exactly as trained.
  - Load checkpoint from `/app/models/model.pth` and apply `checkpoint["model_state_dict"]`.
  - `model.eval()`, CPU `map_location="cpu"`.
- [ ] 7) Implement inference preprocessing consistent with training:
  - PIL image → `RGB`
  - Resize to `224x224`
  - ToTensor + Normalize(mean=[0.5,0.5,0.5], std=[0.5,0.5,0.5])
  - Forward pass → logits → sigmoid prob
  - Threshold → decision mapping (e.g. `prob>=CAT_THRESHOLD => approved`, else `rejected`; choose semantics and document it)
- [ ] 8) Wire FastStream (RabbitMQ) with explicit, durable topology:
  - Ingress:
    - exchange `RabbitExchange("x.moderation.ingress", type=TOPIC, durable=True)`
    - queue `RabbitQueue("q....", durable=True, routing_key=settings.ingress_routing_key)`
  - Result (declare so publishes can’t be unroutable):
    - declare exchange `x.moderation.result` (DIRECT, durable)
    - declare queue `q.moderation.job.result` durable, bind with routing key `moderation.job.result`
  - Ack strategy:
    - Use `ack_policy=AckPolicy.NACK_ON_ERROR` for transient exceptions (requeue).
    - For “expected” failures (bad payload, 404), publish `failed` result and return normally (message gets acked).
    - Only raise for truly transient failures you want to retry (timeouts, publish failure, etc.).
- [ ] 9) Publish result with required metadata:
  - `correlation_id`: copy inbound `message.correlation_id`
  - headers include `{"x-service-name": settings.service_name}`
  - `persist=True`, `mandatory=True`
  - Consider setting FastStream `Channel(on_return_raises=True)` so unroutable publishes fail fast.
- [ ] 10) Add `services/moderation_image_catornotclassifier/Dockerfile`:
  - Base: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
  - `WORKDIR /app`, `COPY . /app`, `RUN uv sync --frozen` (or `uv sync`)
  - `CMD ["uv", "run", "faststream", "run", "app.__main__:app"]`
- [ ] 11) Add docker-compose service + model volume mount:
  - Build context: `./services/moderation_image_catornotclassifier`
  - Env: `AMQP_URL=amqp://guest:guest@rabbitmq:5672/%2F`, `S3_ENDPOINT=http://seaweed-s3:8333`, creds, routing key/queue names, etc.
  - Volume: `./ai/catornot_imageclassifier/outputs:/app/models:ro`
  - Labels: `domain=moderation` (if you want aggregator to count it)
  - `depends_on`: `rabbitmq` + `seaweed-s3`

## Testing and validation
- Local quick run (outside Docker): `cd services/moderation_image_catornotclassifier && uv run faststream run app.__main__:app --reload`
- Docker: `docker compose up -d rabbitmq seaweed-s3 moderation-image-catornotclassifier`
- Publish a test job:
  - send to exchange `x.moderation.ingress` with routing key you chose
  - body: `{"payload":"safu-forum-images/uploads/<file>.jpg"}` (or your real payload format)
  - set `correlation_id` to a known value
- Validate:
  - worker logs show download + inference + publish
  - message is acked (queue depth returns to 0)
  - `q.moderation.job.result` receives a result with `x-service-name` header
  - aggregator/back-end completes the job (if wired)

## Risks and edge cases
- Aggregator expected-workers coupling: adding this worker may cause jobs to never finalize unless each job yields results from every counted service (or you change aggregator logic).
- Payload ambiguity: URL vs `bucket/key` vs key-only; decide and enforce formats.
- S3 transient failures vs permanent failures: choose which ones requeue.
- Big/invalid images: add size/type checks to avoid memory bombs or PIL issues.
- Torch dependency weight: image size and build time will jump; consider CPU-only and pin versions.

## Open questions
- Should this worker subscribe to `moderation.job.text` (as stated) or `moderation.job.image` (name suggests)?
- Will `moderation_text_toxicornotclassifier` remain running at the same time? (If yes, confirm aggregator expectations.)
- What’s the exact `payload` string format from backend (example)?
- What moderation semantics do you want: “cat = approved” and “not cat = rejected”, or something else?
