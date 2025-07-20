from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from core.schemas.base import Base
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
    PrimaryKeyConstraint
)
import uuid
from sqlalchemy.sql import func
from core.schemas.v1.enum import (
    severity_enum,
    action_type_enum,
    SeverityEnum,
    ActionTypeEnum
)
from core.schemas.base import BaseObject

class LogStats(BaseModel):
    stats: Optional[Dict[str, int]] = {}

class AuditLog(BaseObject):
    """Base object of AuditLog"""
    id: Optional[str] = str(uuid.uuid4())
    session_id: Optional[str] = None
    action_type: str
    resource_type: str
    resource_id: Optional[str] = None
    severity: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class LogFilterParams(BaseObject):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    action_type: Optional[str] = None
    resource_type: Optional[str] = None
    severity: Optional[str] = None
    keyword: Optional[str] = None
    limit: int = 10
    offset: int = 0

class AuditLogTable(Base):
    """This is the table for loging information of logs.

    This table also need to be indexed in several composition index for faster searching.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        # PrimaryKeyConstraint('id', 'timestamp', name='pk_audit_logs'),
        Index("ix_audit_logs_tenant_log", "tenant_id", "id"),
        Index("ix_audit_logs_tenant", "tenant_id"),
        Index("ix_audit_logs_severity", "severity"),
        Index("ix_audit_logs_action_type", "action_type"),
        Index("ix_audit_logs_timestamp", "timestamp"),

        # Need to consider again for this partition
        # {"postgresql_partition_by": "RANGE (timestamp)"}
    )

    id = Column(
        String,
        primary_key=True,
        default=str(uuid.uuid4()),
        index=True,
    )
    tenant_id = Column(
        String,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        String,
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action_type = Column(action_type_enum, nullable=False, default=ActionTypeEnum.VIEW)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    severity = Column(severity_enum, nullable=False, default=SeverityEnum.INFO)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
