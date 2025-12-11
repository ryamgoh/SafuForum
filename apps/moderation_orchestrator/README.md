# ContentOrchestratorService (template)

Lightweight FastAPI + aio-pika scaffold for the ContentOrchestratorService. It ingests content moderation requests, fans out to text and image detectors (local or external), aggregates the results, persists the decision, and emits a final moderation event.

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

## Env vars
- `RABBITMQ_URL` (required) – AMQP connection string.
- `TEXT_REQUEST_QUEUE` (default `q.text.moderation`) – queue to consume `Moderation.Orchestrator.AnalysisTextRequested.v1`.
- `TEXT_COMPLETED_EXCHANGE` (default `ex.analysis.text.completed`) – exchange for `Moderation.TextModerationService.AnalysisCompleted.v1`.
- `DETECTOR_MODE` – `in-process` or `workers` (future).
- `COMPOSITE_TIMEOUT_SECONDS` – overall timeout for detector fan-out.

## Architecture (EDA)
- Input: `Content.ProcessRequested` event from ContentService (e.g., published to `q.content.process` or topic `content.process.*`).
- Orchestrator fan-out:
  - Publish `Moderation.Text.Requested` to text detector services (N of them).
  - Publish `Moderation.Image.Requested` to image detector services (M of them).
  - Use routing keys like `moderation.text.requested` / `moderation.image.requested`, with `reply_to` pointing at orchestrator reply queues and `correlation_id = request_id`.
- Detectors:
  - Consume their modality’s request event, run the model, and publish `Moderation.Text.Completed` / `Moderation.Image.Completed` including `detector_id`, `verdict`, `score`, `details`, and the same `correlation_id`.
- Aggregation (in this service):
  - Listen on reply queues, collect detector responses by `correlation_id`, apply timeouts/minimums, and combine text+image outcomes into a final `allow`/`block`/`review`.
  - Persist the decision (see `schema.dbml`) and emit `Moderation.Content.Completed` back to ContentService.
- Deployment: start with in-process detectors for simplicity; split detectors into separate services when they need independent scaling or model/runtime isolation. Aggregation stays in the orchestrator.

## Next steps
- Implement the orchestration pipeline (fan-out + aggregation) in `application/moderation_service.py` and wire consumers/publishers.
- Finish RabbitMQ adapters in `infrastructure/helpers/messaging.py` (queues, exchanges, reply handling).
- Back `repositories/decisions.py` with Postgres using `schema.dbml`, and add migrations.
- Flesh out the synchronous moderation surface in `routers/moderations.py` or drop it in favor of async-only processing.

Replace the stub functions with working logic and extend the contracts to match the design doc.
