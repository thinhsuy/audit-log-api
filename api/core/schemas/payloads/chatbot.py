from pydantic import BaseModel
from core.agent import AgentResponseFormat
from typing import Optional, List
from core.schemas.v1.chat import Conversation

class GetChatbotPayload(BaseModel):
    query: str

class GetChatbotResponse(BaseModel):
    message: str
    response: Optional[AgentResponseFormat] = None

class GetHistoryResponse(BaseModel):
    message: str
    history: Optional[List[Conversation]] = None