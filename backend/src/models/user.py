"""User model."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="created_by_user", lazy="select")
    tasks = relationship("LocalizationTask", back_populates="user", lazy="select")
    feedback = relationship("UserFeedback", back_populates="created_by_user", lazy="select")

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"