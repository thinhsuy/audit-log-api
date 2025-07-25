from core.schemas.base import Base, BaseObject
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
import uuid
from sqlalchemy.sql import func
from typing import Dict, List
from core.schemas.v1.enum import ChatRoleEnum
from openai.types.chat import ChatCompletionMessageToolCall


class Conversation(BaseObject):
    role: ChatRoleEnum
    content: str
    tenant_id: str = None
    tool_calls: List[ChatCompletionMessageToolCall] = None

    def chat_format_dump(self) -> Dict:
        format = {"role": self.role, "content": self.content}
        if self.tool_calls:
            format.update({"tool_calls": self.tool_calls})
        return format


class ConverationTable(Base):
    """Conversation table to store history of chat"""

    __tablename__ = "converations"
    __table_args__ = (
        Index("ix_conversations_tenant_id", "tenant_id"),
        Index("ix_conversations_tenant_role", "tenant_id", "role"),
    )

    id = Column(
        String,
        primary_key=True,
        default=str(uuid.uuid4()),
        index=True,
    )
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    tenant_id = Column(
        String,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
