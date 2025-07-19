from core.config import AUDIT_USER_DB_URL, logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from core.schemas import Base

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

    # async def filter_logs(
    #     self,
    #     tenant_id: str,
    #     params: LogFilterParams,
    #     db: AsyncSession
    # ) -> List[AuditLogTable]:
    #     q = select(AuditLogTable).where(AuditLogTable.tenant_id == tenant_id)

    #     if params.start_date:
    #         q = q.where(AuditLogTable.timestamp >= params.start_date)
    #     if params.end_date:
    #         q = q.where(AuditLogTable.timestamp <= params.end_date)
    #     if params.action_type:
    #         q = q.where(AuditLogTable.action_type == params.action_type)
    #     if params.resource_type:
    #         q = q.where(AuditLogTable.resource_type == params.resource_type)
    #     if params.severity:
    #         q = q.where(AuditLogTable.severity == params.severity)
    #     if params.keyword:
    #         q = q.where(
    #             (AuditLogTable.resource_type.ilike(f"%{params.keyword}%")) |
    #             (cast(AuditLogTable.meta_data, String).ilike(f"%{params.keyword}%"))
    #         )

    #     q = q.order_by(AuditLogTable.timestamp.desc()) \
    #          .offset(params.offset) \
    #          .limit(params.limit)

    #     result = await db.execute(q)
    #     return result.scalars().all()