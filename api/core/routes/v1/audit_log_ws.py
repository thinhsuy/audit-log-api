from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from core.services.authentication import AuthenService
from core.database.CRUD import PGRetrieve
from fastapi.encoders import jsonable_encoder
import asyncio
import traceback

router = APIRouter()


@router.websocket("/stream")
async def log_stream(websocket: WebSocket):
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

    await websocket.accept()
    sessionmaker = websocket.app.state.db_sessionmaker

    try:
        while True:
            async with sessionmaker() as db:
                logs = await PGRetrieve(db).retrieve_logs(
                    tenant_id=token_data["tenant_id"], skip=0, limit=10
                )
            for log in logs:
                await websocket.send_json(
                    {
                        "type": "log.view",
                        "log": jsonable_encoder(log.model_dump()),
                    }
                )

            await asyncio.sleep(1)

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
