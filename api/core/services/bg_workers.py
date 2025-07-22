import time
import json
from core.services import Audit_SQS
from abc import ABC, abstractmethod
from core.database.CRUD import PGRetrieve
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import (
    ERROR_THRESHOLD,
    WARNING_THRESHOLD,
    CRITICAL_THRESHOLD,
    VIETNAM_TZ
)
from core.schemas.v1.enum import SeverityEnum
from datetime import datetime
from core.services import Audit_SQS

class Worker(ABC):
    def __init__(self, db: AsyncSession, **kwargs):
        self.db = db

    @abstractmethod
    async def process(self, payload: dict) -> None:
        """Process payload"""
        raise NotImplementedError("Subclasses must implement process() method")

class StatsWorker(Worker):
    def __init__(self, alert_thresholds: dict = None):
        super().__init__()
        self.thresholds = alert_thresholds or {
            SeverityEnum.ERROR: ERROR_THRESHOLD,
            SeverityEnum.CRITICAL: CRITICAL_THRESHOLD,
            SeverityEnum.WARNING: WARNING_THRESHOLD,
        }
    
    async def process(self, payload):
        tenant_id = payload.get("tenant_id", None)
        if not tenant_id:
            return

        logs_stat = await PGRetrieve(self.db).get_logs_stats_alert(
            tenant_id=tenant_id,
            time_retention=24
        )

        for level, count in logs_stat.stats.items():
            threshold = self.thresholds.get(level)
            if threshold is not None and count > threshold:
                alert_payload = {
                    "event_type": "log.alert",
                    "tenant_id": tenant_id,
                    "severity": level,
                    "count": count,
                    "timestamp": datetime.now(VIETNAM_TZ).isoformat()
                }
                try:
                    Audit_SQS.send_message(alert_payload)
                    print(f"[Stats][ALERT] {level} count {count} > threshold {threshold}")
                except Exception as e:
                    print(f"[Stats][ALERT][ERROR] {e}")

class BackgroundWorkers:
    def __init__(self):
        self.poll_interval: float = 1.0
        self.sqs_max_mess: int = 5
        self.sqs_wait_sec: int = 10
        self.sqs_visi_timeout: int = 30

    def worker_loop(self, db: AsyncSession):
        """Forever loop background recieving messages from SQS"""
        stats_worker = StatsWorker(db=db)
        while True:
            msgs = Audit_SQS.receive_messages(
                self.sqs_max_mess, self.sqs_wait_sec, self.sqs_visi_timeout
            )
            for msg in msgs:
                try:
                    body: dict = json.loads(msg["Body"])
                    type = body.get("type", None)
                    if not type:
                        continue

                    if type == "logs.created":
                        stats_worker.process(payload=body)

                    Audit_SQS.delete_message(msg["ReceiptHandle"])
                except Exception as e:
                    print(f"[WORKER][ERROR] {e}")
                    continue
            time.sleep(self.poll_interval)