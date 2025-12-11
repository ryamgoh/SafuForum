# TextModerationService (template)

Lightweight FastAPI + aio-pika scaffold for the TextModerationService composite. This is intentionally incomplete—wire your actual detectors, hygiene, and persistence on top of this skeleton.

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
- `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` – S3-compatible storage config.
- `DETECTOR_MODE` – `in-process` or `workers` (future).
- `COMPOSITE_TIMEOUT_SECONDS` – overall timeout for detector fan-out.

## Next steps
- Implement the `application/moderation_service.py` pipeline and call it from `workers/text_requested.py`.
- Finish `infrastructure/` adapters (RabbitMQ, Redis locks, S3/text fetch) and thread them through settings.
- Back `repositories/decisions.py` with a real database/table schema and add migrations.
- Flesh out the synchronous moderation surface in `routers/moderations.py` or drop it in favor of async-only processing.

Replace the stub functions with working logic and extend the contracts to match the design doc.
