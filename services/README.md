# Services Template

This directory will host the runnable services for the SafuForum stack. Each service lives in its own folder with its own Dockerfile and dependencies. Use `text_moderation/` as a starter layout for other services (image moderation, content, user, assignment, etc.).

## Suggested layout per service
- `app.py` (or equivalent entrypoint) bootstraps the HTTP server and background consumers.
- `messaging.py` encapsulates RabbitMQ bindings (consumers/producers).
- `config.py` centralizes env vars and defaults.
- `hygiene.py` or similar contains input normalization for that domain.
- `detectors/` (moderation composites) wraps per-detector logic; other services can replace with domain-specific modules.
- `tests/` holds unit/integration tests for that service.

Add more folders as needed (e.g., `db/`, `repositories/`, `schemas/`). Keep external contracts stable with the event names defined in `Implementation.md` and `content-moderation-implementation.md`.
