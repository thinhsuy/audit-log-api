from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from core.config import VIETNAM_TZ
from core.schemas.v1.logs import AuditLogTable
from sqlalchemy import delete
from core.config import logger

class PGDeletion:
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def cleanup_old_logs(
        self, tenant_id: str, retention_days: int = 1
    ) -> int:
        try:
            """Clean up `retention days` logs based on tenant_id"""
            cutoff_date = datetime.now(VIETNAM_TZ) - timedelta(
                days=retention_days
            )
            query = delete(AuditLogTable).where(
                AuditLogTable.tenant_id == tenant_id,
                AuditLogTable.timestamp < cutoff_date,
            )
            result = await self.db.execute(query)
            await self.db.commit()
            return int(result.rowcount)
        except Exception as e:
            logger.error(
                f"Error during cleanup_old_logs for tenant {tenant_id}: {e}"
            )
            await self.db.rollback()
