"""SQLAlchemy ORM models matching schema.dbml."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for ORM models."""


class Status(str, enum.Enum):
    """Status of a moderation job or task."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"

class Verdict(str, enum.Enum):
    """Possible moderation verdicts."""
    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"
    ERROR = "error"

class ModerationJob(Base):
    """Entry point for every moderation job."""

    __tablename__ = "moderation_jobs"
    __table_args__ = ()

    correlating_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Correlation id carried in inbound/outbound events.",
    )
    content_id: Mapped[str | None] = mapped_column(String, nullable=True)
    submitter_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status"),
        nullable=False,
        default=Status.PENDING,
        server_default=text("'pending'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    job_tasks: Mapped[list["JobTask"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    decision: Mapped["ModerationDecision"] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        uselist=False,
        passive_deletes=True,
    )
    text_data: Mapped["TextData"] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        uselist=False,
        passive_deletes=True,
    )
    image_data: Mapped["ImageData"] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        uselist=False,
        passive_deletes=True,
    )


class JobTask(Base):
    """One row per configured service (moderator) for a job."""

    __tablename__ = "job_tasks"
    __table_args__ = (
        UniqueConstraint(
            "correlating_id",
            "event_name",
            name="uq_job_tasks_job_event",
        ),
        Index("ix_job_tasks_job_status", "correlating_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    correlating_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_jobs.correlating_id", ondelete="CASCADE"),
        nullable=False,
    )
    event_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status"),
        nullable=False,
        default=Status.PENDING,
        server_default=text("'pending'"),
    )
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped[ModerationJob] = relationship(back_populates="job_tasks")


class ModerationDecision(Base):
    """Aggregated decision persisted for audits and replay."""

    __tablename__ = "moderation_decisions"

    correlating_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_jobs.correlating_id", ondelete="CASCADE"),
        primary_key=True,
    )
    final_verdict: Mapped[Verdict] = mapped_column(Enum(Verdict, name="verdict"), nullable=False)
    timed_out: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    job: Mapped[ModerationJob] = relationship(back_populates="decision")


class TextData(Base):
    """Stored text content or excerpt for a job."""

    __tablename__ = "text_data"

    correlating_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_jobs.correlating_id", ondelete="CASCADE"),
        primary_key=True,
    )
    text_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    job: Mapped[ModerationJob] = relationship(back_populates="text_data")


class ImageData(Base):
    """Stored image reference for a job."""

    __tablename__ = "image_data"

    correlating_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_jobs.correlating_id", ondelete="CASCADE"),
        primary_key=True,
    )
    image_uri: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    job: Mapped[ModerationJob] = relationship(back_populates="image_data")
