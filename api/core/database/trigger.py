from sqlalchemy import text
from core.config import logger
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
import traceback

from sqlalchemy import text
from core.config import logger
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
import traceback


class PGTrigger:
    def __init__(
        self, conn: AsyncConnection = None, db: AsyncSession = None
    ):
        self.conn: AsyncConnection = conn
        self.db: AsyncSession = db

    async def create_masking_triggers(self):
        """
        Create triggers for masking data to UserTable,
        After insert into UserTable, it need to mask data and then
        store the original data into authorized table to trackback.

        First, insert raw data into MaskedUserTable.
        Then, mask the email and insert into UserTable.
        """
        try:
            if not self.conn:
                raise Exception("Connection is not established")

            # Drop the trigger if it exists
            drop_trigger_query = """
            DROP TRIGGER IF EXISTS trigger_mask_and_store_email ON users;
            """
            await self.conn.execute(text(drop_trigger_query))

            # Create function to mask email and store raw data
            trigger_function = """
            CREATE OR REPLACE FUNCTION mask_and_store_email()
            RETURNS TRIGGER AS $$
            BEGIN  
                INSERT INTO masked_user (user_id, masked_email, created_at)
                VALUES (
                    NEW.id,
                    NEW.email,
                    CURRENT_TIMESTAMP
                );

                NEW.email := CONCAT(SUBSTRING(NEW.email FROM 1 FOR 1), '****', SUBSTRING(NEW.email FROM POSITION('@' IN NEW.email) FOR LENGTH(NEW.email) - POSITION('@' IN NEW.email) + 1));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """

            trigger_query = """
            CREATE TRIGGER trigger_mask_and_store_email
            BEFORE INSERT ON users
            FOR EACH ROW
            EXECUTE FUNCTION mask_and_store_email();
            """

            await self.conn.execute(text(trigger_function))
            await self.conn.execute(text(trigger_query))

        except Exception:
            logger.error(
                f"Failed to create trigger: {traceback.format_exc()}"
            )
            raise Exception("Failed to create trigger")
