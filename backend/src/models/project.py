"""Project, Branch, and Tag models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import BaseModel


class Project(BaseModel):
    """Project model for repository configuration."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    repository_url: Mapped[str] = mapped_column(Text, nullable=False)
    repository_type: Mapped[str] = mapped_column(
        Enum(
            "gerrit", "repo", "codehub", "github", "gitlab", 
            name="repository_type"
        ), 
        nullable=False
    )
    default_branch: Mapped[str] = mapped_column(
        String(100), default="main", nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    created_by_user = relationship("User", back_populates="projects", lazy="select")
    branches = relationship(
        "Branch", back_populates="project", cascade="all, delete-orphan", lazy="select"
    )
    tags = relationship(
        "Tag", back_populates="project", cascade="all, delete-orphan", lazy="select"
    )
    tasks = relationship(
        "LocalizationTask", back_populates="project", cascade="all, delete-orphan", lazy="select"
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint("repository_url", "name", name="uq_project_repo_name"),
        Index("ix_projects_created_by", "created_by"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Project(id={self.id}, name={self.name}, type={self.repository_type})>"


class Branch(BaseModel):
    """Branch model for project branches."""

    __tablename__ = "branches"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_commit_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project = relationship("Project", back_populates="branches", lazy="select")
    tags = relationship(
        "Tag", back_populates="branch", cascade="all, delete-orphan", lazy="select"
    )
    tasks = relationship(
        "LocalizationTask", back_populates="branch", cascade="all, delete-orphan", lazy="select"
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_branch_project_name"),
        Index("ix_branches_project", "project_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Branch(id={self.id}, name={self.name}, project_id={self.project_id})>"


class Tag(BaseModel):
    """Tag model for version tags."""

    __tablename__ = "tags"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("branches.id", ondelete="CASCADE"), 
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    commit_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    tag_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    author_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sequence_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tags", lazy="select")
    branch = relationship("Branch", back_populates="tags", lazy="select")
    good_tasks = relationship(
        "LocalizationTask",
        foreign_keys="[LocalizationTask.good_tag_id]",
        back_populates="good_tag",
        lazy="select"
    )
    bad_tasks = relationship(
        "LocalizationTask", 
        foreign_keys="[LocalizationTask.bad_tag_id]",
        back_populates="bad_tag",
        lazy="select"
    )
    final_tasks = relationship(
        "LocalizationTask",
        foreign_keys="[LocalizationTask.final_problematic_tag_id]", 
        back_populates="final_problematic_tag",
        lazy="select"
    )
    build_jobs = relationship("BuildJob", back_populates="tag", lazy="select")

    # Table constraints
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_tag_project_name"),
        Index("ix_tags_project_sequence", "project_id", "branch_id", "sequence_number"),
        Index("ix_tags_sequence", "project_id", "sequence_number"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Tag(id={self.id}, name={self.name}, project_id={self.project_id})>"