from pydantic import BaseModel
from typing import Optional, List
from core.schemas.v1.logs import AuditLog

class CreateLogPayload(AuditLog):
    pass

class LogEntryCreateResponse(BaseModel):
    message: str
    log: Optional[dict] = None

class GetLogsResponse(BaseModel):
    message: str
    logs: Optional[List[AuditLog]] = None

class GetLogResponse(BaseModel):
    message: str
    log: Optional[AuditLog] = None