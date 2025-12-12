# Moderation Orchestrator Data Model

Simplified schema for tracking moderation jobs and their per-service tasks. See `schema.dbml` for the authoritative structure.

## Core Entities
- `moderation_jobs`: One row per incoming moderation job (`correlating_id`). Holds optional content/submitter metadata plus job status and timestamps.
- `text_data` / `image_data`: Optional per-job content references (text excerpt or image URI) keyed by `correlating_id`.
- `job_tasks`: One row per configured event target for a job. Insert rows at job start; update status and payload (raw service event) as events arrive. Linked to `moderation_jobs` via `correlating_id`.
- `moderation_decisions`: Aggregated outcome for a job. Stores final verdict, timeout flag, and decided timestamp.

## Enums
- `status`: `pending`, `completed`, `failed`, `timed_out`.
- `verdict`: `allow`, `block`, `review`, `error`.

## Relationships and Constraints
- `job_tasks.correlating_id` → FK to `moderation_jobs.correlating_id` with ON DELETE CASCADE; unique `(correlating_id, event_name)` so each event target contributes at most once per job.
- `text_data.correlating_id` / `image_data.correlating_id` → FK to `moderation_jobs.correlating_id` with ON DELETE CASCADE (optional per-job content).
- `moderation_decisions.correlating_id` → PK/FK to `moderation_jobs.correlating_id` with ON DELETE CASCADE (one decision per job).

## Lifecycle Notes
1. Ingest: create `moderation_jobs` (`status = pending`), seed `job_tasks` for configured services, and publish requests.
2. Fan-out responses: upon each completion event, update the matching `job_tasks` row (status + payload).
3. Aggregate: when all tasks reach a terminal state (or a decisive block/timeout policy triggers), compute the final decision, insert/update `moderation_decisions`, and mark the job accordingly.
4. Publish: emit completion event (per `events.md`).

## Operational Considerations
- **Timeouts**: a periodic reaper can mark stale `job_tasks` as `failed`/`timed_out` equivalents and finalize jobs per policy.
- **Auditability**: `payload` JSONB on `job_tasks` and final decision fields support debugging; apply retention/PII scrubbing as needed.
- **Indexes**: `(correlating_id, event_name)` and `(correlating_id, status)` support aggregation queries.
- **Timestamps**: Prefer DB-enforced `updated_at` via a trigger: define `set_updated_at()` that sets `NEW.updated_at = now()` and attach it `BEFORE UPDATE` on tables that need it (e.g., `moderation_jobs`, `job_tasks`).

## SQLAlchemy mapping notes

- Column setup: `mapped_column(...)` declares a DB column. Common kwargs:
    - `primary_key=True` makes it the PK. `UUID(as_uuid=True)`/`Integer` pick the DB type.
    - `nullable=False` vs `nullable=True` controls NOT NULL.
    - `default=...` is a Python-side default applied when inserting via SQLAlchemy only.
    - `server_default=text("...")` sets the DB default (applies to all writers, including raw SQL/migrations).
    - `Enum(Status, name="status")` maps the Python enum to a named PostgreSQL enum type; the name is the DB type name.
- Status/enum reuse: Both `moderation_jobs.status` and `job_tasks.status` use the same `Status` enum with DB type name `status`, so there’s a single PostgreSQL enum shared by both columns.
- Timestamps: `DateTime(timezone=True)` stores timestamptz. `server_default=func.now()` sets `DEFAULT now()` in the DB. `onupdate=func.now()` is an ORM-side hook; to enforce DB-wide, use a trigger (as noted in the doc).
- FKs and cascades:
    - `ForeignKey("moderation_jobs.id", ondelete="CASCADE")` tells PostgreSQL to delete child rows when a parent is deleted (DB-level).
    - `relationship(..., cascade="all, delete-orphan")` tells the ORM to delete children when removed via the session.
    - `passive_deletes=True` on relationships defers to the DB for cascades, avoiding double work by the ORM.
- Relationships: `relationship(back_populates="job")` wires two models together. `uselist=False` makes it one-to-one (`decision`, `text_data`, `image_data`). Lists (e.g., `job_tasks`) are one-to-many.
- Indexes/constraints:
    - `UniqueConstraint("correlating_id", "event_name", name="uq_job_tasks_job_event")` enforces one task per event target per job.
    - `Index("ix_job_tasks_job_status", "correlating_id", "status")` is a multi-column index to speed queries filtering by job and status.
