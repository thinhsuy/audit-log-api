from fastapi import Depends, APIRouter, HTTPException, WebSocketDisconnect, WebSocket
from core.services.authentication import AuthenService
from core.config import logger
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_get_db
from core.database.CRUD import PGCreation, PGRetrieve
from core.services.websocket import WS_MANAGER, WS_SERVICE
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated
import asyncio

router = APIRouter()

TokenDependencies = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]

@router.websocket("/stream")
async def log_streaming(
    websocket: WebSocket,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")

        tenant_id = token_data.get("tenant_id", None)
        user_id = token_data.get("user_id", None)
        
        if not tenant_id or not user_id:
            await WS_SERVICE.send_message(
                session_id=tenant_id,
                message_package={
                    "type": "error.authentication",
                    "message": "Unauthorized: Missing tenant_id or user_id."
                })
            return

        await WS_MANAGER.connect(
            websocket=websocket,
            session_id=tenant_id
        )
        while True:
            logs = await PGRetrieve(db).retrieve_logs(tenant_id=tenant_id)
            if logs:
                for log in logs:
                    await WS_SERVICE.send_message(
                        session_id=tenant_id,
                        message_package={
                            "type": "log.view",
                            "log": log.model_dump()
                        }
                    )

            await asyncio.sleep(1)
        
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from log stream.")
    except Exception as e:
        logger.error(f"Error during log streaming: {traceback.format_exc()}")
        await websocket.send_text("An error occurred while streaming logs.")
        await websocket.close()

    finally:
        if tenant_id:
            WS_MANAGER.disconnect(websocket=websocket, session_id=tenant_id)
