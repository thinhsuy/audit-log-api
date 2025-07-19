from core.schemas.base import Base, BaseObject
from sqlalchemy import (
    Column,
    String,
    DateTime
)
import uuid
from sqlalchemy.sql import func
from typing import Optional

class Tenant(BaseObject):
    name: Optional[str] = None

class TenantTable(Base):
    """Tenant table to store information of tenants"""
    __tablename__ = "tenants"

    id = Column(
        String,
        primary_key=True,
        default=str(uuid.uuid4()),
        index=True,
    )
    name = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )