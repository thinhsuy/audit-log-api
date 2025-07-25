from sqlalchemy import text
from core.config import logger
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
import traceback


class PGPermission:
    def __init__(
        self, conn: AsyncConnection = None, db: AsyncSession = None
    ):
        self.conn: AsyncConnection = conn
        self.db: AsyncSession = db

    async def grant_permissions(self, table_name: str, role: str):
        """
        Grand permission only access to specific table
        from specific role
        """
        try:
            if not self.conn:
                raise Exception("Connection is not established")

            grant_query = f"""
                GRANT SELECT ON {table_name} TO {role};
            """

            await self.conn.execute(text(grant_query))
            await self.conn.commit()
        except Exception:
            logger.error(
                f"Failed to grant permissions: {traceback.format_exc()}"
            )
            raise Exception("Failed to create permission")
