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
from sqlalchemy import String
from core.schemas.v1.enum import user_role_enum, UserRoleEnum
from core. schemas.base import BaseObject

class User(BaseObject):
    tenant_id: str
    username: str
    email: Optional[str] = None
    role: UserRoleEnum = None

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
        default=str(uuid.uuid4()),
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
    role = Column(user_role_enum, default=UserRoleEnum.CLIENT, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

class MaskedUser(Base):
    __tablename__ = "masked_user"
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_masked_email'),
    )
    user_id = Column(String, primary_key=True, nullable=False)
    masked_email = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)