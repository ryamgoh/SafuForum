# Moderation Orchestrator Service

Lightweight FastAPI + aio-pika scaffold for the Moderation Orchestrator Service. It ingests content moderation requests, fans out to configured moderators/services, aggregates the results, persists the decision, and emits a final moderation event.

## How to run (dev)

### Local
```bash
fastapi dev main.py
```

```bash
# sync deps into .venv using uv (fast)
uv venv .venv
. .venv/bin/activate
# uv pip install -r requirements.txt
or: uv sync  # uses pyproject.toml

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Env vars (Not all implemented yet)
- `RABBITMQ_URL` (required) – AMQP connection string.
- `TEXT_REQUEST_QUEUE` (default `q.text.moderation`) – queue to consume `Moderation.Orchestrator.AnalysisTextRequested.v1`.
- `TEXT_COMPLETED_EXCHANGE` (default `ex.analysis.text.completed`) – exchange for `Moderation.TextModerationService.AnalysisCompleted.v1`.
- `DETECTOR_MODE` – `in-process` or `workers` (future).
- `COMPOSITE_TIMEOUT_SECONDS` – overall timeout for detector fan-out.

## Architecture (EDA)
- Input: `Content.ProcessRequested` event from ContentService (e.g., published to `q.content.process` or topic `content.process.*`).
- Content-based routing:
  - Inspect the incoming content. If it has text, fan out to text services; if it has an image, fan out to image services; if both, fan out to both sets.
- Normalized content storage:
  - `moderation_jobs` holds core metadata (ids/status/timestamps).
  - `text_data` (1:1 via `job_id`) holds text content/excerpt.
  - `image_data` (1:1 via `job_id`) holds the image URI/object key.
- Orchestrator fan-out:
  - For each required service (e.g., `Deepfake_V1`, `TextSafe_V2`), insert a `job_tasks` row and publish a request message carrying `correlation_id = job_id` and `service_id`.
  - Use routing keys like `moderation.text.requested` / `moderation.image.requested`, pointing at each service’s queue/exchange.
- Moderators/services:
  - Consume their request event, run the model, and publish a completion event including `service_id`, `verdict`, `score`, `details` (in payload), and the same `correlation_id`.
- Aggregation (in this service):
  - On each completion event, update the matching `job_tasks` row (store the raw response payload). When all tasks reach a terminal state (or an early block/timeout policy triggers), combine outcomes into a final `allow`/`block`/`review`.
  - Persist the decision (see `schema.dbml`) and emit `Moderation.Job.Completed` back to ContentService (see `events.md`).
- Deployment: start with a few in-process services for simplicity; split them into separate services when they need independent scaling or model/runtime isolation. Aggregation stays in the orchestrator.
