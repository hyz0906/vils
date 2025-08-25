"""Service configuration models."""

from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..database.base import BaseModel


class ServiceConfig(BaseModel):
    """Model for external service configurations."""

    __tablename__ = "service_configs"

    service_type: Mapped[str] = mapped_column(String(100), nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "service_type", "service_name", name="uq_service_type_name"
        ),
        Index("ix_service_active", "service_type", "is_active"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ServiceConfig(id={self.id}, type={self.service_type}, name={self.service_name})>"