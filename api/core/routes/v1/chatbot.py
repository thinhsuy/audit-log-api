from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_get_db
from core.schemas.payloads.chatbot import *
from core.agent.tools import (
    AUDIT_LOG_FUNCTION_SPEC,
    AUDIT_LOG_FUNCTIONS_LIST,
)
from core.agent.prompt import MASTER_PROMPT
from core.agent.engine_client import ENGINE, AZURE_CLIENT
from core.schemas.v1.chat import Conversation
from core.schemas.v1.enum import ChatRoleEnum
from core.agent import SmartAgent, ToolAdditionalParams
from core.services.authentication import AuthenService
from core.agent.tool_format import AgentResponseFormat
from core.database.CRUD import PGCreation, PGRetrieve
from core.config import logger
import traceback
from core.limiter import RATE_LIMITER

router = APIRouter()
Limiter = RATE_LIMITER.get_limiter()

TokenDependencies = Annotated[
    HTTPAuthorizationCredentials, Depends(HTTPBearer())
]

AGENT = SmartAgent(
    engine=ENGINE,
    client=AZURE_CLIENT,
    functions_list=AUDIT_LOG_FUNCTIONS_LIST,
    functions_spec=AUDIT_LOG_FUNCTION_SPEC,
)


@router.post(
    "/",
    description="Get chat response with Agent",
    response_model=GetChatbotResponse,
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def get_chat_response(
    payload: GetChatbotPayload,
    request: Request,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db),
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )

        tenant_id = token_data.get("tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=401, detail="Invalid tenant_id."
            )

        history = await PGRetrieve(db).retrieve_chat_history(
            tenant_id=tenant_id,
            limit=4,  # only get 4 nearest conversations
        )
        response: AgentResponseFormat = await AGENT.run(
            user_input=payload.query,
            conversation=[
                Conversation(
                    role=ChatRoleEnum.SYSTEM, content=MASTER_PROMPT
                )
            ]
            + history,
            additional_params=ToolAdditionalParams(
                {"tenant_id": tenant_id}
            ),
        )

        if response:
            await PGCreation(db).create_bulk_conversations(
                tenant_id=tenant_id,
                conversations=[
                    Conversation(
                        role=ChatRoleEnum.USER, content=payload.query
                    ),
                    Conversation(
                        role=ChatRoleEnum.ASSISTANT,
                        content=response.content,
                    ),
                ],
            )
            return GetChatbotResponse(
                message="Get response successfully!", response=response
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Cannot get the response currently",
            )

    except HTTPException:
        raise
    except Exception:
        message = "Failed to get response from chatbot agent!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)


@router.get(
    "/",
    description="Get history chat (tenant-scoped)",
    response_model=GetHistoryResponse,
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def get_chat_response(
    token: TokenDependencies,
    request: Request,
    db: AsyncSession = Depends(async_get_db),
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )

        tenant_id = token_data.get("tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=401, detail="Invalid tenant_id."
            )

        history = await PGRetrieve(db).retrieve_chat_history(
            tenant_id=tenant_id
        )

        return GetHistoryResponse(
            message="Retrieve chat history successfully!",
            history=history,
        )

    except HTTPException:
        raise
    except Exception:
        message = "Failed to get chat history from chatbot agent!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)
