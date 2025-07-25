from core.schemas import Base
from sqlalchemy import Column, DateTime, ForeignKey, Index, String
import uuid
from sqlalchemy.sql import func
from core.schemas.base import BaseObject
from typing import Optional
from datetime import datetime


class Session(BaseObject):
    tenant_id: str
    user_id: str
    access_token: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class SessionTable(Base):
    """
    Session table to store information of login session of user + tenant,
        which also need to be indexed for faster search.
    """

    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_tenant_user", "tenant_id", "user_id"),
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
    access_token = Column(String, nullable=False)
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)
