"""Task-related models."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import BaseModel


class LocalizationTask(BaseModel):
    """Task model for issue localization sessions."""

    __tablename__ = "localization_tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    good_tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False
    )
    bad_tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False
    )
    
    status: Mapped[str] = mapped_column(
        Enum("active", "paused", "completed", "failed", name="task_status"),
        nullable=False,
        default="active"
    )
    
    total_tags_in_range: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_iteration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    final_problematic_tag_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="tasks", lazy="select")
    project = relationship("Project", back_populates="tasks", lazy="select")
    branch = relationship("Branch", back_populates="tasks", lazy="select")
    
    good_tag = relationship(
        "Tag", 
        foreign_keys=[good_tag_id],
        back_populates="good_tasks",
        lazy="select"
    )
    bad_tag = relationship(
        "Tag",
        foreign_keys=[bad_tag_id], 
        back_populates="bad_tasks",
        lazy="select"
    )
    final_problematic_tag = relationship(
        "Tag",
        foreign_keys=[final_problematic_tag_id],
        back_populates="final_tasks",
        lazy="select"
    )
    
    iterations = relationship(
        "TaskIteration",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="select"
    )
    build_jobs = relationship(
        "BuildJob",
        back_populates="task", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    feedback = relationship(
        "UserFeedback",
        back_populates="task",
        cascade="all, delete-orphan", 
        lazy="select"
    )
    session = relationship(
        "TaskSession",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint("bad_tag_id != good_tag_id", name="check_different_tags"),
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_created_desc", "created_at"),
        Index("ix_tasks_user_active", "user_id", "status").postgresql_where(
            lambda: LocalizationTask.status == "active"
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<LocalizationTask(id={self.id}, name={self.task_name}, status={self.status})>"


class TaskIteration(BaseModel):
    """Model for tracking binary search iterations."""

    __tablename__ = "task_iterations"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("localization_tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    iteration_number: Mapped[int] = mapped_column(Integer, nullable=False)
    search_range_start: Mapped[int] = mapped_column(Integer, nullable=False)
    search_range_end: Mapped[int] = mapped_column(Integer, nullable=False)
    candidates_generated: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    selected_candidates: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    task = relationship("LocalizationTask", back_populates="iterations", lazy="select")
    build_jobs = relationship(
        "BuildJob",
        back_populates="iteration",
        cascade="all, delete-orphan",
        lazy="select"
    )
    feedback = relationship(
        "UserFeedback",
        back_populates="iteration", 
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "search_range_end > search_range_start", name="check_range_valid"
        ),
        Index("ix_iterations_task", "task_id", "iteration_number"),
        Index("ix_iterations_task_number", "task_id", "iteration_number", unique=True),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaskIteration(id={self.id}, task_id={self.task_id}, iteration={self.iteration_number})>"


class TaskSession(BaseModel):
    """Model for storing task session state."""

    __tablename__ = "task_sessions"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("localization_tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    session_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    current_range_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_range_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default="now()",
        nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    task = relationship("LocalizationTask", back_populates="session", lazy="select")

    # Table constraints
    __table_args__ = (
        Index("ix_sessions_expires", "expires_at"),
        Index("ix_sessions_task", "task_id", unique=True),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaskSession(id={self.id}, task_id={self.task_id})>"