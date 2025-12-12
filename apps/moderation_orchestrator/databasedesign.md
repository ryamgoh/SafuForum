# Moderation Orchestrator Data Model

Simplified schema for tracking moderation jobs and their per-service tasks. See `schema.dbml` for the authoritative structure.

## Core Entities
- `moderation_jobs`: One row per incoming moderation job (`id` correlation). Holds content metadata (e.g., `has_text`, `has_image`) and the inbound `payload` used for routing/fan-out, plus job status and timestamps.
- `job_tasks`: One row per configured service for a job. Insert rows at job start; update status and payload (raw service event) as events arrive. Linked to `moderation_jobs`.
- `moderation_decisions`: Aggregated outcome for a job. Stores final verdict/score, rationale, timeout flag, and count of tasks considered.

## Enums
- `status`: `pending`, `completed`, `failed`, `timed_out`.
- `verdict`: `allow`, `block`, `review`, `error`.

## Relationships and Constraints
- `job_tasks.job_id` → FK to `moderation_jobs.id`; unique `(job_id, service_id)` so each service contributes at most once per job.
- `moderation_decisions.job_id` → PK/FK to `moderation_jobs.id` (one decision per job).

## Lifecycle Notes
1. Ingest: create `moderation_jobs` (`status = pending`), seed `job_tasks` for configured services, and publish requests.
2. Fan-out responses: upon each completion event, update the matching `job_tasks` row (status + payload).
3. Aggregate: when all tasks reach a terminal state (or a decisive block/timeout policy triggers), compute the final decision, insert/update `moderation_decisions`, and mark the job accordingly.
4. Publish: emit completion event (per `events.md`).

## Operational Considerations
- **Timeouts**: a periodic reaper can mark stale `job_tasks` as `failed`/`timed_out` equivalents and finalize jobs per policy.
- **Auditability**: `payload` JSONB on `job_tasks` and `rationale` on `moderation_decisions` support debugging; apply retention/PII scrubbing as needed.
- **Indexes**: `(job_id, service_id)` and `(job_id, status)` support aggregation queries.
