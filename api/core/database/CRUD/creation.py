from core.config import VIETNAM_TZ, logger
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from core.schemas.v1.session import SessionTable, Session
from core.schemas.v1.logs import AuditLogTable, AuditLog
from core.schemas.v1.tenant import Tenant, TenantTable
from core.schemas.v1.user import User, UserTable
import asyncpg
import traceback
from sqlalchemy.exc import SQLAlchemyError

class PGCreation:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_bulk_logs(
        self,
        logs: list[AuditLog],
        tenant_id: str,
        user_id: str,
    ) -> list[AuditLog]:
        try:
            entries = []
            for log in logs:
                data = log.model_dump(exclude_none=True)
                data.update({
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                })
                data.setdefault("timestamp", datetime.now(VIETNAM_TZ))
                entries.append(AuditLogTable(**data))

            self.db.add_all(entries)
            await self.db.commit()

            for entry in entries:
                await self.db.refresh(entry)
            return logs

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(f"Invalid enum value error when creating bulk logs: {traceback.format_exc()}")
            return None

        except SQLAlchemyError as e:
            logger.error(f"Database error when creating bulk logs: {traceback.format_exc()}")
            return None

        except Exception as e:
            logger.error(f"Error when creating bulk logs: {traceback.format_exc()}")
            return None

    async def create_new_log(
        self,
        log: AuditLog,
        tenant_id: str,
        user_id: str,
    ) -> AuditLogTable:
        try:
            data = log.model_dump(exclude_none=True)
            data.update({
                "tenant_id": tenant_id,
                "user_id": user_id,
            })
            data.setdefault("timestamp", datetime.now(VIETNAM_TZ))
            entry = AuditLogTable(**data)
            self.db.add(entry)
            await self.db.commit()
            await self.db.refresh(entry)
            return entry
        
        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(f"Invalid enum value error when creating log: {traceback.format_exc()}")
            return None

        except SQLAlchemyError as e:
            logger.error(f"Database error when creating log: {traceback.format_exc()}")
            return None

        except Exception as e:
            logger.error(f"Error when creating log: {traceback.format_exc()}")
            return None
        
    async def create_new_session(
        self,
        session: Session,
    ) -> Session:
        try:
            data = session.model_dump()
            new_sess = SessionTable(**data)
            self.db.add(new_sess)
            await self.db.commit()
            await self.db.refresh(new_sess)
            return Session.model_validate(new_sess)
        except Exception:
            logger.error(f"Error when create new session: {traceback.format_exc()}")
            return None

    async def create_new_tenant(
        self,
        tenant: Tenant
    ) -> Tenant:
        try:
            new_tenant = TenantTable(
                id=tenant.id,
                name=tenant.name
            )
            self.db.add(new_tenant)
            await self.db.commit()
            await self.db.refresh(new_tenant)
            return tenant

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(f"Invalid enum value error when creating log: {traceback.format_exc()}")
            return None

        except SQLAlchemyError as e:
            logger.error(f"Database error when creating log: {traceback.format_exc()}")
            return None

        except Exception as e:
            logger.error(f"Error when creating log: {traceback.format_exc()}")
            return None

    async def create_new_user(
        self,
        user: User
    ) -> UserTable:
        try:
            data = user.model_dump()
            new_user = UserTable(**data)
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(f"Invalid enum value error when creating log: {traceback.format_exc()}")
            return None

        except SQLAlchemyError as e:
            logger.error(f"Database error when creating log: {traceback.format_exc()}")
            return None

        except Exception as e:
            logger.error(f"Error when creating log: {traceback.format_exc()}")
            return None