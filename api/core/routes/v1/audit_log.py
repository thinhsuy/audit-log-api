from fastapi import APIRouter, Depends, HTTPException, Header
from core.models import LogEntry, LogEntryCreateResponse, GetLogResponse
from core.security.access_token import verify_token
from core.config import logger
import traceback
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.postgres_intialization import async_get_db
from core.database.postgres_crud import PostgresCRUD

router = APIRouter()

tokenDep = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]

@router.post(
    "/logs",
    description="Create log entry (with tenant ID)",
    response_model=LogEntryCreateResponse)
async def get_log(
    payload: LogEntry,
    token: tokenDep,
    db: AsyncSession = Depends(async_get_db),
):
    try:
        token_data = verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        
        user_id = token_data["sub"]
        tenant_id = token_data["tenant_id"]
        _ = await PostgresCRUD().create_log(log=payload, db=db)
        return LogEntryCreateResponse(
            message="Create Log Successfully!",
            user_id=user_id,
            tenant_id=tenant_id
        )
    except Exception as e:
        message = "Failed to create log."
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)
    

@router.get(
    "/logs",
    description="Search/filter logs (tenant-scoped)",
    # response_model=List[LogEntry],
)
async def get_logs(
    token: tokenDep,
    db: AsyncSession = Depends(async_get_db)
):
    token_data = verify_token(token.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    tenant_id = token_data["tenant_id"]
    
    response = await PostgresCRUD().filter_logs(
        tenant_id=tenant_id,
        db=db
    )
    if not response:
        raise HTTPException(status_code=404, detail="No logs found.")
    
    return response
