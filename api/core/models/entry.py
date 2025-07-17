from pydantic import BaseModel
from typing import Optional

class LogEntry(BaseModel):
    action_type: str
    resource_type: str
    resource_id: int
    user_id: int
    severity: str
    tenant_id: str
    timestamp: Optional[str] = None

class LogEntryCreateResponse(BaseModel):
    message: str
    user_id: str
    tenant_id: str

class GetLogResponse(BaseModel):
    tenant_id: str
    limit: Optional[int] = 10
    skip: Optional[int] = 0