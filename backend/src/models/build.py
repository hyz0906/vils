"""Build and feedback models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import BaseModel


class BuildJob(BaseModel):
    """Model for tracking build jobs."""

    __tablename__ = "build_jobs"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("localization_tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    iteration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_iterations.id", ondelete="CASCADE"),
        nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False
    )
    
    external_build_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    build_service: Mapped[str] = mapped_column(String(100), nullable=False)
    build_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "running", "success", "failed", "cancelled",
            name="build_status"
        ),
        nullable=False,
        default="pending"
    )
    
    logs_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifacts_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    task = relationship("LocalizationTask", back_populates="build_jobs", lazy="select")
    iteration = relationship("TaskIteration", back_populates="build_jobs", lazy="select")
    tag = relationship("Tag", back_populates="build_jobs", lazy="select")
    feedback = relationship(
        "UserFeedback",
        back_populates="build_job",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Table constraints
    __table_args__ = (
        Index("ix_builds_task_iteration", "task_id", "iteration_id"),
        Index("ix_builds_status_created", "status", "created_at"),
        Index("ix_builds_pending", "status", "created_at").postgresql_where(
            lambda: BuildJob.status == "pending"
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<BuildJob(id={self.id}, service={self.build_service}, status={self.status})>"


class UserFeedback(BaseModel):
    """Model for user feedback on builds."""

    __tablename__ = "user_feedback"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("localization_tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    iteration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_iterations.id", ondelete="CASCADE"),
        nullable=False
    )
    build_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("build_jobs.id", ondelete="CASCADE"),
        nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False
    )
    
    feedback_type: Mapped[str] = mapped_column(
        Enum("working", "broken", "inconclusive", name="feedback_type"),
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    task = relationship("LocalizationTask", back_populates="feedback", lazy="select")
    iteration = relationship("TaskIteration", back_populates="feedback", lazy="select")
    build_job = relationship("BuildJob", back_populates="feedback", lazy="select")
    created_by_user = relationship("User", back_populates="feedback", lazy="select")

    # Table constraints
    __table_args__ = (
        Index("ix_feedback_task_iteration", "task_id", "iteration_id"),
        Index("ix_feedback_recent", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserFeedback(id={self.id}, type={self.feedback_type}, task_id={self.task_id})>"