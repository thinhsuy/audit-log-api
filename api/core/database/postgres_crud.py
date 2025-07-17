from core.database.schemas import LogEntryTable
from core.config import VIETNAM_TZ
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.session import AsyncSession
from core.models import LogEntry

class PostgresCRUD:
    def __init__(self):
        pass
    
    async def create_log(self, log: LogEntry, db: AsyncSession):
        log_entry = LogEntryTable(
            action_type=log.action_type,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            user_id=log.user_id,
            severity=log.severity,
            tenant_id=log.tenant_id,
            timestamp=log.timestamp or str(datetime.now(VIETNAM_TZ))
        )
        
        db.add(log_entry)
        await db.commit()
    
    async def filter_logs(self, tenant_id: str,  db: AsyncSession):
        query = await db.execute(
            select(LogEntryTable)\
                .where(LogEntryTable.tenant_id == tenant_id)
        )
        return query.scalars().all()