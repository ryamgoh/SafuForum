"""V1

Revision ID: 445a25912f5a
Revises: 0ade6ddf1f14
Create Date: 2025-12-12 10:42:40.788082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '445a25912f5a'
down_revision: Union[str, Sequence[str], None] = '0ade6ddf1f14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Clean up any partial runs: drop new-schema tables if they exist
    for table_name in [
        "job_tasks",
        "moderation_decisions",
        "text_data",
        "image_data",
        "moderation_jobs",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")

    # Clean up enums
    op.execute("DROP TYPE IF EXISTS status CASCADE")
    op.execute("DROP TYPE IF EXISTS verdict CASCADE")

    # Drop legacy tables from the initial revision
    for table_name in [
        "outbox_events",
        "moderator_runs",
        "moderation_decisions",
        "moderation_requests",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")

    op.execute("DROP INDEX IF EXISTS ix_moderator_runs_request_modality")

    # Drop legacy enums if present
    for enum_name in [
        "outboxstatus",
        "moderatorstatus",
        "moderatormodality",
        "requeststatus",
        "contentkind",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name} CASCADE")

    # New enums (create if missing)
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE status AS ENUM ('pending', 'completed', 'failed', 'timed_out');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE verdict AS ENUM ('allow', 'block', 'review', 'error');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
        """
    )

    status_enum = sa.dialects.postgresql.ENUM(
        "pending",
        "completed",
        "failed",
        "timed_out",
        name="status",
        create_type=False,
    )
    verdict_enum = sa.dialects.postgresql.ENUM(
        "allow",
        "block",
        "review",
        "error",
        name="verdict",
        create_type=False,
    )

    # moderation_jobs
    op.create_table(
        "moderation_jobs",
        sa.Column("correlating_id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_id", sa.String(), nullable=True),
        sa.Column("submitter_id", sa.String(), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # text_data
    op.create_table(
        "text_data",
        sa.Column("correlating_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation_jobs.correlating_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("text_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # image_data
    op.create_table(
        "image_data",
        sa.Column("correlating_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation_jobs.correlating_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("image_uri", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # job_tasks
    op.create_table(
        "job_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("correlating_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation_jobs.correlating_id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_name", sa.String(length=128), nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("payload", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("correlating_id", "event_name", name="uq_job_tasks_job_event"),
    )
    op.create_index("ix_job_tasks_job_status", "job_tasks", ["correlating_id", "status"], unique=False)

    # moderation_decisions
    op.create_table(
        "moderation_decisions",
        sa.Column("correlating_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("moderation_jobs.correlating_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("final_verdict", verdict_enum, nullable=False),
        sa.Column("timed_out", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("moderation_decisions")
    op.drop_index("ix_job_tasks_job_status", table_name="job_tasks")
    op.drop_table("job_tasks")
    op.drop_table("image_data")
    op.drop_table("text_data")
    op.drop_table("moderation_jobs")

    op.execute("DROP TYPE IF EXISTS status CASCADE")
    op.execute("DROP TYPE IF EXISTS verdict CASCADE")
