from core.services.simple_queue import SimpleQueueService
from core.config import AUDIT_QUEUE_URL

Audit_SQS = SimpleQueueService(AUDIT_QUEUE_URL)

__all__ = [
    "Audit_SQS"
]