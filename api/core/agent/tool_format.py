from pydantic import BaseModel
from typing import List
from core.schemas.v1.chat import Conversation


class ToolCallFormat(BaseModel):
    tool_call_id: str
    role: str
    function_name: str
    content: str


class ToolResponseFormat(BaseModel):
    content: str
    kwargs: dict = {}

    def get_kwargs(self, key: str) -> any:
        if self.kwargs.get(key):
            return self.kwargs.get(key)
        return None


class ToolAdditionalParams:
    def __init__(self, args: dict) -> None:
        self.args = args

    def get_kwargs(self, key: str) -> any:
        if self.args.get(key):
            return self.args.get(key)
        return None


class AgentResponseFormat(BaseModel):
    content: str
    conversation: List[Conversation] = None
    tool_results: List[ToolResponseFormat] = None
    tool_called: List[ToolCallFormat] = None
