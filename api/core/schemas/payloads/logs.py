from pydantic import BaseModel
from typing import Optional, List
from core.schemas.v1.logs import AuditLog
from core.schemas.v1.logs import LogStats

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

class BulkLogCreateResponse(BaseModel):
    message: str
    logs: List[AuditLog]

class CleanupLogPayload(BaseModel):
    retention_days: int

class CleanupLogResponse(BaseModel):
    message: str
    deleted_count: Optional[int] = None

class GetLogsStatsResponse(BaseModel):
    message: str
    response: Optional[LogStats] = None