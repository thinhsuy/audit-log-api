from sqlalchemy.ext.asyncio import AsyncSession
from core.schemas.v1.tenant import TenantTable, Tenant
from core.schemas.v1.user import  UserTable, User
from core.schemas.v1.logs import AuditLogTable, AuditLog
from typing import List
from sqlalchemy import select

class PGRetrieve:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def retrieve_tenant(
        self,
        tenant_name: str = None,
        tenant_id: str = None
    ) -> Tenant:
        query = select(TenantTable)
        if tenant_id: 
            query = query.where(TenantTable.id == tenant_id)
        if tenant_name:
            query = query.where(TenantTable.name == tenant_name)
        q_t = await self.db.execute(query)
        tenant_table = q_t.scalar_one_or_none()
        return Tenant.model_validate(tenant_table) if tenant_table else None

    async def retrieve_user(
        self,
        username: str = None,
        user_id: str = None
    ) -> User:
        query = select(UserTable)
        if user_id: 
            query = query.where(UserTable.id == user_id)
        if username:
            query = query.where(UserTable.username == username)
        q_t = await self.db.execute(query)
        user_table = q_t.scalar_one_or_none()
        return User.model_validate(user_table) if user_table else None

    async def retrieve_logs(
        self,
        tenant_id: str = None,
        user_id: str = None,
        log_id: str = None,
        is_get_one: bool = False,
    ) -> List[AuditLog]:
        query = select(AuditLogTable)
        if tenant_id:
            query.where(AuditLogTable.tenant_id == tenant_id)
        if user_id:
            query.where(AuditLogTable.user_id == user_id)
        if log_id:
            query.where(AuditLogTable.id == log_id)
        
        result = await self.db.execute(query)

        if is_get_one:
            log_table = result.scalar()
            return AuditLog.model_validate(log_table) if log_table else None

        return [
            AuditLog.model_validate(log_table)
            for log_table in result.scalars().all()
        ]

    async def retrieve_tenants(
        self,
        tenant_name: str = None,
        tenant_id: str = None,
        is_get_one: bool = False
    ) -> List[Tenant]:
        query = select(TenantTable)
        if tenant_name:
            query.where(TenantTable.name == tenant_name)
        if tenant_id:
            query.where(TenantTable.id == tenant_id)
        
        result = await self.db.execute(query)
        if is_get_one:
            tenant_table = result.scalar()
            return Tenant.model_validate(tenant_table) if tenant_table else None
        
        return [
            Tenant.model_validate(tenant_table)
            for tenant_table in result.scalars().all()
        ]
