"""
database/db.py - Async SQLAlchemy engine and session factory for AgroGuard-AI.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Async engine
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,          # Set True to log SQL statements during development
    pool_pre_ping=True,
    poolclass=NullPool,  # Recommended for async/serverless workloads
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncSession:  # type: ignore[return]
    """
    FastAPI dependency: yields a database session and ensures cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all ORM-mapped tables and migrate missing columns if needed."""
    from app.database.models import Base  # local import avoids circular deps
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Automatically ensure pre-existing tables have updated columns
    columns_to_add = [
        ("google_id", "VARCHAR(255)"),
        ("auth_provider", "VARCHAR(50) DEFAULT 'PASSWORD'"),
        ("village", "VARCHAR(255)"),
        ("district", "VARCHAR(255)"),
        ("state", "VARCHAR(255) DEFAULT 'Tamil Nadu'"),
        ("is_active", "BOOLEAN DEFAULT true"),
    ]
    for col_name, col_def in columns_to_add:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"ALTER TABLE farmers ADD COLUMN IF NOT EXISTS {col_name} {col_def};"))
        except Exception as exc:
            logger.debug("Migration column %s skipped: %s", col_name, exc)

    logger.info("Database tables created / verified.")
