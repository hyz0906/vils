"""Database connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from ..config import settings


def create_database_engine():
    """Create synchronous database engine for migrations."""
    return create_engine(
        str(settings.database_url),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        pool_recycle=300,
    )


def create_async_engine_instance():
    """Create asynchronous database engine."""
    # Convert sync URL to async URL
    database_url = str(settings.database_url).replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    
    return create_async_engine(
        database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug,
    )


# Create engines
engine = create_database_engine()
async_engine = create_async_engine_instance()

# Create session factories
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_database() -> Session:
    """Get synchronous database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


async def get_async_database() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with context manager."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()