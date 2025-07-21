from core.schemas import Base
from core.database.trigger import PGTrigger
from sqlalchemy.ext.asyncio import AsyncEngine
from core.config import logger

async def init_db(engine: AsyncEngine):
    """Establish database along with setups information around"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized and tables created.")

        await PGTrigger(conn=conn).create_masking_triggers()
        logger.info("Triggers and functions created successfully.")
