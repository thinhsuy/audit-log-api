from sqlalchemy.ext.asyncio import AsyncSession
from core.schemas.v1.tenant import TenantTable, Tenant
from core.schemas.v1.user import UserTable, User
from core.schemas.v1.logs import AuditLogTable, AuditLog
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.sql import func
from core.schemas.v1.enum import (
    SeverityEnum,
    ActionTypeEnum,
    LogStatsEnum,
)
from core.schemas.v1.logs import LogStats
from datetime import datetime, timedelta
from core.config import VIETNAM_TZ
from core.schemas.v1.enum import SeverityEnum
from core.services.security import SecurityService
from core.schemas.v1.chat import ConverationTable, Conversation
from core.config import logger
import traceback


class PGRetrieve:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve_logs(
        self,
        tenant_id: str = None,
        user_id: str = None,
        log_id: str = None,
        skip: int = None,
        limit: int = None,
        order_by_time: bool = True,
    ) -> List[AuditLog]:
        try:
            query = select(AuditLogTable)
            if tenant_id:
                query = query.where(
                    AuditLogTable.tenant_id == tenant_id
                )
            if user_id:
                query = query.where(AuditLogTable.user_id == user_id)
            if log_id:
                query = query.where(AuditLogTable.id == log_id)

            if order_by_time:
                query = query.order_by(AuditLogTable.timestamp.desc())
            if skip and limit:
                query = query.offset(skip).limit(limit)

            res = await self.db.execute(query)
            records = res.scalars().all()

            logs: List[AuditLog] = []
            for rec in records:
                # rec.meta_data is a cipher text
                raw = rec.meta_data
                if isinstance(raw, str) and raw:
                    try:
                        rec.meta_data = (
                            SecurityService().decrypt_field(raw)
                        )
                    except Exception:
                        rec.meta_data = None

                # convert SQLAlchemy obj → Pydantic model
                logs.append(AuditLog.model_validate(rec))
            return logs
        except Exception:
            logger.error(
                f"Failed to retrieve logs: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return []

    async def retrieve_tenant(
        self, tenant_name: str = None, tenant_id: str = None
    ) -> Tenant:
        try:
            query = select(TenantTable)
            if tenant_id:
                query = query.where(TenantTable.id == tenant_id)
            if tenant_name:
                query = query.where(TenantTable.name == tenant_name)
            q_t = await self.db.execute(query)
            tenant_table = q_t.scalar_one_or_none()
            return (
                Tenant.model_validate(tenant_table)
                if tenant_table
                else None
            )
        except Exception:
            logger.error(
                f"Failed to retrieve tenant: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

    async def retrieve_user(
        self, username: str = None, user_id: str = None
    ) -> User:
        try:
            query = select(UserTable)
            if user_id:
                query = query.where(UserTable.id == user_id)
            if username:
                query = query.where(UserTable.username == username)
            q_t = await self.db.execute(query)
            user_table = q_t.scalar_one_or_none()
            return (
                User.model_validate(user_table) if user_table else None
            )
        except Exception:
            logger.error(
                f"Failed to retrieve user: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

    async def retrieve_tenants(
        self,
        tenant_name: str = None,
        tenant_id: str = None,
        is_get_one: bool = False,
    ) -> List[Tenant]:
        try:
            query = select(TenantTable)
            if tenant_name:
                query.where(TenantTable.name == tenant_name)
            if tenant_id:
                query.where(TenantTable.id == tenant_id)

            result = await self.db.execute(query)
            if is_get_one:
                tenant_table = result.scalar()
                return (
                    Tenant.model_validate(tenant_table)
                    if tenant_table
                    else None
                )

            return [
                Tenant.model_validate(tenant_table)
                for tenant_table in result.scalars().all()
            ]
        except Exception:
            logger.error(
                f"Failed to retrieve tenants: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return []

    async def get_logs_stats_by_tenant(
        self, tenant_id: str
    ) -> LogStats:
        """This would return total logs have been occured in the whole time of tenent"""
        try:
            field_names = [
                LogStatsEnum.TOTOL_LOGS,
                LogStatsEnum.INFO_LOGS,
                LogStatsEnum.WARN_LOGS,
                LogStatsEnum.ERROR_LOGS,
                LogStatsEnum.CRITICAL_lOGS,
                LogStatsEnum.CREATE_LOGS,
                LogStatsEnum.UPDATE_LOGS,
                LogStatsEnum.DELETE_LOGS,
                LogStatsEnum.VIEW_LOGS,
            ]

            query = select(
                func.count().label(LogStatsEnum.TOTOL_LOGS),
                func.count()
                .filter(AuditLogTable.severity == SeverityEnum.INFO)
                .label(LogStatsEnum.INFO_LOGS),
                func.count()
                .filter(AuditLogTable.severity == SeverityEnum.WARNING)
                .label(LogStatsEnum.WARN_LOGS),
                func.count()
                .filter(AuditLogTable.severity == SeverityEnum.ERROR)
                .label(LogStatsEnum.ERROR_LOGS),
                func.count()
                .filter(
                    AuditLogTable.severity == SeverityEnum.CRITICAL
                )
                .label(LogStatsEnum.CRITICAL_lOGS),
                func.count()
                .filter(
                    AuditLogTable.action_type == ActionTypeEnum.CREATE
                )
                .label(LogStatsEnum.CREATE_LOGS),
                func.count()
                .filter(
                    AuditLogTable.action_type == ActionTypeEnum.UPDATE
                )
                .label(LogStatsEnum.UPDATE_LOGS),
                func.count()
                .filter(
                    AuditLogTable.action_type == ActionTypeEnum.DELETE
                )
                .label(LogStatsEnum.DELETE_LOGS),
                func.count()
                .filter(
                    AuditLogTable.action_type == ActionTypeEnum.VIEW
                )
                .label(LogStatsEnum.VIEW_LOGS),
            ).where(AuditLogTable.tenant_id == tenant_id)

            result = await self.db.execute(query)
            stats = result.fetchone()

            if not stats:
                return LogStats(stats={})

            stats_dict = {
                field_names[i]: stats[i]
                for i in range(len(field_names))
            }
            return LogStats(stats=stats_dict)
        except Exception:
            logger.error(
                f"Failed to retrieve stats: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

    async def get_logs_stats_alert(
        self, tenant_id: str, time_retention: int = 24
    ) -> LogStats:
        """Get logs stats of Severity and alert whenever a new log created"""
        try:
            now = datetime.now(VIETNAM_TZ)
            window_start = now - timedelta(hours=time_retention)
            severities = [
                SeverityEnum.ERROR,
                SeverityEnum.CRITICAL,
                SeverityEnum.WARNING,
            ]
            counts = {}
            query = (
                select(
                    AuditLogTable.severity,
                    func.count(AuditLogTable.id).label("cnt"),
                )
                .where(
                    AuditLogTable.tenant_id == tenant_id,
                    AuditLogTable.timestamp >= window_start,
                    AuditLogTable.severity.in_(severities),
                )
                .group_by(AuditLogTable.severity)
            )
            result = await self.db.execute(query)
            rows = result.all()
            counts = {level: 0 for level in severities}
            for severity, count in rows:
                counts[severity] = count
            return LogStats(stats=counts)
        except Exception:
            logger.error(
                f"Failed to retrieve stats alert: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

    async def retrieve_chat_history(
        self,
        tenant_id: str,
        order_by_time: bool = True,
        skip: int = None,
        limit: int = None,
    ) -> List[Conversation]:
        try:
            query = select(ConverationTable)
            if tenant_id:
                query = query.where(
                    ConverationTable.tenant_id == tenant_id
                )

            if order_by_time:
                query = query.order_by(
                    ConverationTable.created_at.desc()
                )

            if skip and limit:
                query = query.offset(skip).limit(limit)

            res = await self.db.execute(query)
            records = res.scalars().all()

            return [
                Conversation.model_validate(rec) for rec in records
            ]
        except Exception:
            logger.error(
                f"Failed to retrieve conversation: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return []
