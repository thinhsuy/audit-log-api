from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from core.services.authentication import AuthenService
from core.database.CRUD import PGRetrieve
from fastapi.encoders import jsonable_encoder
import asyncio
import traceback
import json
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
from core.database.CRUD import PGRetrieve
import traceback
import json
import asyncio
from core.config import logger

router = APIRouter()

AGENT = SmartAgent(
    engine=ENGINE,
    client=AZURE_CLIENT,
    functions_list=AUDIT_LOG_FUNCTIONS_LIST,
    functions_spec=AUDIT_LOG_FUNCTION_SPEC,
)

@router.websocket("/stream")
async def log_stream(websocket: WebSocket):
    """Establish websocket connection which also request authetication access header attached for JWT"""
    auth = websocket.headers.get("authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    token_data = AuthenService.verify_token(token)
    if not token_data:
        print("Close when not token_data")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    tenant_id = token_data.get("tenant_id", None)
    if not tenant_id:
        print("Close when not token_data")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await websocket.accept()
    sessionmaker = websocket.app.state.db_sessionmaker

    try:
        while True:
            msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            parsed = json.loads(msg)

            async with sessionmaker() as db:
                if parsed["type"] == "chat":
                    response: AgentResponseFormat = await AGENT.run(
                        user_input=parsed["query"],
                        conversation=[
                            Conversation(
                                role=ChatRoleEnum.SYSTEM, content=MASTER_PROMPT
                            )
                        ],
                        additional_params=ToolAdditionalParams(
                            {"tenant_id": tenant_id}
                        ),
                    )
                    if response:
                        try:
                            response.content = json.loads(response.content).get("answer")
                        except Exception:
                            logger.warning(f"Cannot convert json package of Agent response: {traceback.format_exc()}")

                        await websocket.send_json(
                            {
                                "type": "chat.response",
                                "response": response.content
                            }
                        )

                logs = await PGRetrieve(db).retrieve_logs(
                    tenant_id=tenant_id, skip=0, limit=10
                )
                await websocket.send_json(
                    {
                        "type": "logs.view",
                        "logs": [
                            jsonable_encoder(log.model_dump())
                            for log in logs
                        ],
                    }
                )

                await asyncio.sleep(2)

                stats = await PGRetrieve(db).get_logs_stats_by_tenant(
                    tenant_id=tenant_id
                )

                await websocket.send_json(
                    {
                        "type": "logs.stats",
                        **jsonable_encoder(stats)
                    }
                )
                await asyncio.sleep(2)

    except WebSocketDisconnect:
        return

    except Exception as e:
        print(f"Error in log_stream: {e}\n{traceback.format_exc()}")
        try:
            await websocket.send_json(
                {
                    "type": "ws.error",
                    "message": "Internal server error during streaming.",
                }
            )
        except:
            pass

    finally:
        try:
            await websocket.close()
        except:
            pass
