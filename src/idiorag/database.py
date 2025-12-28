"""Database models and session management."""

from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import DateTime, String, Text, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from .config import get_settings

# Global engine and session factory
engine = None
async_session_factory = None

# Get schema from settings
settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    # Use the configured schema for all tables (from DATABASE_SCHEMA env var)
    __table_args__ = {"schema": settings.database_schema}


class Document(Base):
    """Document model representing uploaded documents for RAG."""
    
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column(type_=Text, nullable=True)  # JSON stored as text
    doc_type: Mapped[str] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"Document(id={self.id}, user_id={self.user_id}, title={self.title[:50]})"


async def init_db() -> None:
    """Initialize database connection and create tables.
    
    Note: In production, use Alembic for migrations instead of create_all.
    """
    global engine, async_session_factory
    
    settings = get_settings()
    
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=not settings.is_production,
    )
    
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create schema if it doesn't exist
    async with engine.begin() as conn:
        # Create schema
        await conn.execute(
            text(f"CREATE SCHEMA IF NOT EXISTS {settings.database_schema}")
        )
        
        # Create tables (for development only)
        # In production, use Alembic migrations
        if not settings.is_production:
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    global engine
    
    if engine:
        await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    if not async_session_factory:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
