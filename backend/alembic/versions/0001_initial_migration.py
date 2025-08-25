"""Initial migration - Create all tables

Revision ID: 0001
Revises: 
Create Date: 2024-08-25 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database."""
    # Create custom enums
    task_status_enum = postgresql.ENUM(
        "active", "paused", "completed", "failed", name="task_status"
    )
    task_status_enum.create(op.get_bind())

    build_status_enum = postgresql.ENUM(
        "pending", "running", "success", "failed", "cancelled", name="build_status"
    )
    build_status_enum.create(op.get_bind())

    feedback_type_enum = postgresql.ENUM(
        "working", "broken", "inconclusive", name="feedback_type"
    )
    feedback_type_enum.create(op.get_bind())

    repository_type_enum = postgresql.ENUM(
        "gerrit", "repo", "codehub", "github", "gitlab", name="repository_type"
    )
    repository_type_enum.create(op.get_bind())

    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    
    # Create indexes for users
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # Create projects table
    op.create_table(
        "projects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("repository_url", sa.Text, nullable=False),
        sa.Column("repository_type", repository_type_enum, nullable=False),
        sa.Column("default_branch", sa.String(100), nullable=False, default="main"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.UniqueConstraint("repository_url", "name", name="uq_project_repo_name"),
    )
    
    # Create indexes for projects
    op.create_index("ix_projects_created_by", "projects", ["created_by"])

    # Create branches table
    op.create_table(
        "branches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("last_commit_hash", sa.String(64), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "name", name="uq_branch_project_name"),
    )
    
    # Create indexes for branches
    op.create_index("ix_branches_project", "branches", ["project_id"])

    # Create tags table
    op.create_table(
        "tags",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "branch_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("commit_hash", sa.String(64), nullable=False),
        sa.Column("tag_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("author_email", sa.String(255), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("sequence_number", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "name", name="uq_tag_project_name"),
    )
    
    # Create indexes for tags
    op.create_index(
        "ix_tags_project_sequence", "tags", ["project_id", "branch_id", "sequence_number"]
    )
    op.create_index("ix_tags_sequence", "tags", ["project_id", "sequence_number"])

    # Create localization_tasks table
    op.create_table(
        "localization_tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "branch_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "good_tag_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "bad_tag_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("status", task_status_enum, nullable=False, default="active"),
        sa.Column("total_tags_in_range", sa.Integer, nullable=True),
        sa.Column("current_iteration", sa.Integer, nullable=False, default=0),
        sa.Column(
            "final_problematic_tag_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("resolution_notes", sa.Text, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["good_tag_id"], ["tags.id"]),
        sa.ForeignKeyConstraint(["bad_tag_id"], ["tags.id"]),
        sa.ForeignKeyConstraint(["final_problematic_tag_id"], ["tags.id"]),
        sa.CheckConstraint("bad_tag_id != good_tag_id", name="check_different_tags"),
    )
    
    # Create indexes for localization_tasks
    op.create_index("ix_tasks_user_status", "localization_tasks", ["user_id", "status"])
    op.create_index("ix_tasks_created_desc", "localization_tasks", ["created_at"])

    # Create task_iterations table
    op.create_table(
        "task_iterations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "task_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("iteration_number", sa.Integer, nullable=False),
        sa.Column("search_range_start", sa.Integer, nullable=False),
        sa.Column("search_range_end", sa.Integer, nullable=False),
        sa.Column("candidates_generated", postgresql.JSONB, nullable=False),
        sa.Column("selected_candidates", postgresql.JSONB, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["localization_tasks.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "search_range_end > search_range_start", name="check_range_valid"
        ),
        sa.UniqueConstraint("task_id", "iteration_number", name="ix_iterations_task_number"),
    )
    
    # Create indexes for task_iterations
    op.create_index("ix_iterations_task", "task_iterations", ["task_id", "iteration_number"])

    # Create build_jobs table
    op.create_table(
        "build_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "task_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "iteration_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "tag_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("external_build_id", sa.String(255), nullable=True),
        sa.Column("build_service", sa.String(100), nullable=False),
        sa.Column("build_url", sa.Text, nullable=True),
        sa.Column("status", build_status_enum, nullable=False, default="pending"),
        sa.Column("logs_url", sa.Text, nullable=True),
        sa.Column("artifacts_url", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["localization_tasks.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["iteration_id"], ["task_iterations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
    )
    
    # Create indexes for build_jobs
    op.create_index("ix_builds_task_iteration", "build_jobs", ["task_id", "iteration_id"])
    op.create_index("ix_builds_status_created", "build_jobs", ["status", "created_at"])

    # Create user_feedback table
    op.create_table(
        "user_feedback",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "task_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "iteration_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "build_job_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "tag_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("feedback_type", feedback_type_enum, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["localization_tasks.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["iteration_id"], ["task_iterations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["build_job_id"], ["build_jobs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    
    # Create indexes for user_feedback
    op.create_index("ix_feedback_task_iteration", "user_feedback", ["task_id", "iteration_id"])
    op.create_index("ix_feedback_recent", "user_feedback", ["created_at"])

    # Create task_sessions table
    op.create_table(
        "task_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "task_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True
        ),
        sa.Column("session_data", postgresql.JSONB, nullable=False),
        sa.Column("current_range_start", sa.Integer, nullable=True),
        sa.Column("current_range_end", sa.Integer, nullable=True),
        sa.Column(
            "last_activity",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["localization_tasks.id"], ondelete="CASCADE"
        ),
    )
    
    # Create indexes for task_sessions
    op.create_index("ix_sessions_expires", "task_sessions", ["expires_at"])
    op.create_index("ix_sessions_task", "task_sessions", ["task_id"], unique=True)

    # Create service_configs table
    op.create_table(
        "service_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("service_type", sa.String(100), nullable=False),
        sa.Column("service_name", sa.String(100), nullable=False),
        sa.Column("base_url", sa.Text, nullable=False),
        sa.Column("api_key_encrypted", sa.Text, nullable=True),
        sa.Column("config_data", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("service_type", "service_name", name="uq_service_type_name"),
    )
    
    # Create indexes for service_configs
    op.create_index("ix_service_active", "service_configs", ["service_type", "is_active"])


def downgrade() -> None:
    """Downgrade database."""
    # Drop tables in reverse order
    op.drop_table("service_configs")
    op.drop_table("task_sessions")
    op.drop_table("user_feedback")
    op.drop_table("build_jobs")
    op.drop_table("task_iterations")
    op.drop_table("localization_tasks")
    op.drop_table("tags")
    op.drop_table("branches")
    op.drop_table("projects")
    op.drop_table("users")
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS task_status")
    op.execute("DROP TYPE IF EXISTS build_status")
    op.execute("DROP TYPE IF EXISTS feedback_type")
    op.execute("DROP TYPE IF EXISTS repository_type")