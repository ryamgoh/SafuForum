"""SQLAlchemy ORM models matching schema.dbml."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for ORM models."""


class JobStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    timed_out = "timed_out"


class Verdict(str, enum.Enum):
    allow = "allow"
    block = "block"
    review = "review"
    error = "error"


class ModerationJob(Base):
    """Entry point for every moderation job."""

    __tablename__ = "moderation_jobs"
    __table_args__ = ()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Correlation/job id carried in inbound/outbound events.",
    )
    content_id: Mapped[str | None] = mapped_column(String, nullable=True)
    submitter_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        nullable=False,
        default=JobStatus.pending,
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
    )
    decision: Mapped["ModerationDecision"] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        uselist=False,
    )
    text_data: Mapped["TextData"] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        uselist=False,
    )
    image_data: Mapped["ImageData"] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        uselist=False,
    )


class JobTask(Base):
    """One row per configured service (moderator) for a job."""

    __tablename__ = "job_tasks"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "service_id",
            name="uq_job_tasks_job_service",
        ),
        Index("ix_job_tasks_job_status", "job_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_jobs.id"),
        nullable=False,
    )
    service_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        nullable=False,
        default=JobStatus.pending,
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

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_jobs.id"),
        primary_key=True,
    )
    final_verdict: Mapped[Verdict] = mapped_column(Enum(Verdict), nullable=False)
    final_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    timed_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    task_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    job: Mapped[ModerationJob] = relationship(back_populates="decision")


class TextData(Base):
    """Stored text content or excerpt for a job."""

    __tablename__ = "text_data"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_jobs.id"),
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

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_jobs.id"),
        primary_key=True,
    )
    image_uri: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    job: Mapped[ModerationJob] = relationship(back_populates="image_data")
