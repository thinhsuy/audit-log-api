import asyncio
import json
from core.services import Audit_SQS
from abc import ABC, abstractmethod
from core.database.CRUD import PGRetrieve
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from core.config import (
    ERROR_THRESHOLD,
    WARNING_THRESHOLD,
    CRITICAL_THRESHOLD,
    VIETNAM_TZ,
)
from core.schemas.v1.enum import SeverityEnum
from datetime import datetime
from core.services import Audit_SQS
from core.config import logger
import traceback


class Worker(ABC):
    def __init__(self, db: AsyncSession, **kwargs):
        self.db = db

    @abstractmethod
    async def process(self, payload: dict) -> None:
        """Process payload"""
        raise NotImplementedError(
            "Subclasses must implement process() method"
        )


class StatsWorker(Worker):
    def __init__(
        self, db: AsyncSession, alert_thresholds: dict = None
    ):
        super().__init__(db)
        self.thresholds = alert_thresholds or {
            SeverityEnum.ERROR: ERROR_THRESHOLD,
            SeverityEnum.CRITICAL: CRITICAL_THRESHOLD,
            SeverityEnum.WARNING: WARNING_THRESHOLD,
        }

    async def process(self, payload):
        try:
            tenant_id = payload.get("tenant_id", None)
            if not tenant_id:
                return

            logger.info(
                "[WORKER][STATS] Calculate stats for message:", payload
            )

            logs_stat = await PGRetrieve(self.db).get_logs_stats_alert(
                tenant_id=tenant_id, time_retention=24
            )

            for level, count in logs_stat.stats.items():
                threshold = self.thresholds.get(level)
                if threshold is not None and count > threshold:
                    alert_payload = {
                        "event_type": "logs.alert",
                        "tenant_id": tenant_id,
                        "severity": level,
                        "count": count,
                        "timestamp": datetime.now(
                            VIETNAM_TZ
                        ).isoformat(),
                    }
                    try:
                        Audit_SQS.send_message(alert_payload)
                        logger.warning(
                            f"[WORKER][STAT][ALERT] {level} count {count} > threshold {threshold}"
                        )
                    except Exception as e:
                        logger.error(f"[WORKER][STAT][ERROR] {e}")
        except Exception as e:
            print(f"[WORKER][STAT][ERROR] {e}")


class BackgroundWorkers:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        self.sessionmaker = sessionmaker
        self.poll_interval: float = 1.0
        self.sqs_max_mess: int = 5
        self.sqs_wait_sec: int = 10
        self.sqs_visi_timeout: int = 30

    async def worker_loop(self):
        while True:
            try:
                msgs = await asyncio.to_thread(
                    Audit_SQS.receive_messages,
                    self.sqs_max_mess,
                    self.sqs_wait_sec,
                    self.sqs_visi_timeout,
                )

                if not msgs:
                    await asyncio.sleep(self.poll_interval)
                    continue

                async with self.sessionmaker() as session:
                    for msg in msgs:
                        try:
                            body = json.loads(msg["Body"])
                            evt_type = body.get("type")
                            if evt_type == "logs.created":
                                await StatsWorker(db=session).process(
                                    body
                                )

                            Audit_SQS.delete_message(
                                msg["ReceiptHandle"]
                            )
                        except Exception as e:
                            logger.error(
                                f"[WORKER][MSG ERROR] {e}\n{traceback.format_exc()}"
                            )

                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(
                    f"[WORKER][LOOP ERROR] {e}\n{traceback.format_exc()}"
                )
                await asyncio.sleep(self.poll_interval)
