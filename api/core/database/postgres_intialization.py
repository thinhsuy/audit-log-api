from core.config import AUDIT_USER_DB_URL, logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from core.database.schemas import Base

async_engine = create_async_engine(
    AUDIT_USER_DB_URL,
    pool_size=5,  # Default: 5 connections
    max_overflow=10,  # Default: 10 additional connections
    pool_timeout=30,  # Default: 30 seconds
    pool_recycle=3600,  # Set to -1 by default (no recycling)
    pool_pre_ping=True,  # Default: False
)

async_session = async_sessionmaker(
    async_engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession
)

async def async_get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
        finally:
            await session.close()

async def create_tables():
    """Initialize the database."""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()
            logger.info("Database initialized and tables created.")
    except Exception as ex:
        logger.error(f"Failed to create tables: {ex}")

async def dispose_db():
    """Dispose the database."""
    await async_engine.dispose()

