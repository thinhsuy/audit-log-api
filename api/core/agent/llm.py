from openai import AsyncAzureOpenAI
from typing import List, Annotated
from pydantic import BaseModel
from enum import Enum
import json
from openai.types.chat import ChatCompletionMessageToolCall

class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class Conversation(BaseModel):
    role: RoleEnum
    content: str
    tool_calls: List[ChatCompletionMessageToolCall] = None

class LargeLanguageModel:
    def __init__(self, engine: str, client: AsyncAzureOpenAI):
        self.engine = engine
        self.client = client
        self.history: List[Conversation] = []

    async def get_response(
        self,
        conversation: List[Conversation] = None,
        max_tokens: int = None,
        response_format: dict = {"type": "json_object"}
    ) -> Annotated[str, dict]:
        response = await self.client.chat.completions.create(
            model=self.engine,
            messages=[
                convers.model_dump()
                for convers in conversation
            ],
            max_tokens=max_tokens,
            response_format=response_format
        )
        content = str(response.choices[0].message.content)
        if response_format and response_format.get("type", "") == "json_object":
            return json.loads(content)
        return content