from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from core.config import AUDIT_USER_DB_URL
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi import Request, HTTPException


def get_engine() -> AsyncEngine:
    """Create one Async Engine only which would be allocated by FastAPI state"""
    return create_async_engine(
        AUDIT_USER_DB_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
    )


def get_sessionmaker(engine):
    """Generate a new db_session"""
    return async_sessionmaker(
        engine,
        autocommit=False,
        autoflush=False,
        class_=AsyncSession,
    )


async def async_get_db(request: Request):
    """From FastAPI state, get out the db_session generated"""
    sessionmaker = request.app.state.db_sessionmaker
    async with sessionmaker() as session:
        try:
            yield session
        except Exception as ex:
            await session.rollback()
            raise HTTPException(500, detail="Database error") from ex
