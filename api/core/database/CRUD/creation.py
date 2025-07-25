from core.config import VIETNAM_TZ, logger
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from core.schemas.v1.session import SessionTable, Session
from core.schemas.v1.logs import AuditLogTable, AuditLog
from core.schemas.v1.tenant import Tenant, TenantTable
from core.schemas.v1.user import User, UserTable
import asyncpg
import traceback
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from core.services.security import SecurityService
from typing import List
from core.schemas.v1.chat import Conversation, ConverationTable


class PGCreation:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_tenant_partition(self, tenant_id: str):
        try:
            """Initi tenant partition table for audit_logs"""
            partition_name = f"audit_logs_{tenant_id}"
            sql = f"""
            CREATE TABLE IF NOT EXISTS "{partition_name}"
            PARTITION OF audit_logs FOR VALUES IN ('{tenant_id}');
            """
            await self.db.execute(text(sql))
        except Exception:
            logger.error(
                f"Error when ensuring tenant partition for {tenant_id}: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

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
                data.update(
                    {
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                    }
                )
                data.setdefault("timestamp", datetime.now(VIETNAM_TZ))
                if data.get("meta_data"):
                    data.update(
                        {
                            "meta_data": SecurityService().encrypt_field(
                                data.get("meta_data")
                            )
                        }
                    )
                entries.append(AuditLogTable(**data))

            self.db.add_all(entries)
            await self.db.commit()

            for entry in entries:
                await self.db.refresh(entry)
            return logs

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(
                f"Invalid enum value error when creating bulk logs: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except SQLAlchemyError as e:
            logger.error(
                f"Database error when creating bulk logs: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except Exception as e:
            logger.error(
                f"Error when creating bulk logs: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

    async def create_new_log(
        self,
        log: AuditLog,
        tenant_id: str,
        user_id: str,
    ) -> AuditLog:
        try:
            data = log.model_dump(exclude_none=True)
            data.update({"tenant_id": tenant_id, "user_id": user_id})
            if data.get("meta_data"):
                data.update(
                    {
                        "meta_data": SecurityService().encrypt_field(
                            data.get("meta_data")
                        )
                    }
                )

            data.setdefault("timestamp", datetime.now(VIETNAM_TZ))
            entry = AuditLogTable(**data)
            self.db.add(entry)
            await self.db.commit()
            await self.db.refresh(entry)
            return log

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(
                f"Invalid enum value error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except SQLAlchemyError as e:
            logger.error(
                f"Database error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except Exception as e:
            logger.error(
                f"Error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
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
            logger.error(
                f"Error when create new session: {traceback.format_exc()}"
            )
            return None

    async def create_new_tenant(self, tenant: Tenant) -> Tenant:
        try:
            new_tenant = TenantTable(id=tenant.id, name=tenant.name)
            self.db.add(new_tenant)
            await self.db.commit()
            await self.db.refresh(new_tenant)

            await self.ensure_tenant_partition(tenant_id=tenant.id)
            return tenant

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(
                f"Invalid enum value error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except SQLAlchemyError as e:
            logger.error(
                f"Database error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except Exception as e:
            logger.error(
                f"Error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

    async def create_new_user(self, user: User) -> UserTable:
        try:
            data = user.model_dump()
            new_user = UserTable(**data)
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(
                f"Invalid enum value error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except SQLAlchemyError as e:
            logger.error(
                f"Database error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except Exception as e:
            logger.error(
                f"Error when creating log: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

    async def create_bulk_conversations(
        self, tenant_id: str, conversations: List[Conversation]
    ) -> List[Conversation]:
        try:
            entries = []
            for convers in conversations:
                data = convers.model_dump(exclude_none=True)
                data.update({"tenant_id": tenant_id})
                entries.append(ConverationTable(**data))

            self.db.add_all(entries)
            await self.db.commit()

            for entry in entries:
                await self.db.refresh(entry)

            return conversations

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            logger.error(
                f"Invalid enum value error when creating bulk conversations: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except SQLAlchemyError as e:
            logger.error(
                f"Database error when creating bulk conversations: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None

        except Exception as e:
            logger.error(
                f"Error when creating bulk conversations: {traceback.format_exc()}"
            )
            await self.db.rollback()
            return None
