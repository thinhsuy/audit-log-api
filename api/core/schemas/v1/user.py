from core.schemas.base import Base, BaseObject
from sqlalchemy import (
    Column,
    String,
    DateTime,
    UniqueConstraint,
    ForeignKey
)
import uuid
from sqlalchemy.sql import func
from typing import Optional

class User(BaseObject):
    id: Optional[str] = str(uuid.uuid4())
    tenant_id: str
    username: str
    email: Optional[str] = None

class UserTable(Base):
    """
    User table to store information of user, which need to set id,
        tenant_id and username as unique values
    """
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "username",
            name="uq_users_tenant_username"
        ),
    )
    id = Column(
        String,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    tenant_id = Column(
        String,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )