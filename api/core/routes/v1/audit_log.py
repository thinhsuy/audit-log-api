from fastapi import APIRouter, Depends, HTTPException
from core.schemas.payloads.logs import (
    CreateLogPayload,
    LogEntryCreateResponse,
    GetLogsResponse,
    GetLogResponse
)
from core.services.authentication import AuthenService
from core.config import logger
import traceback
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.base import async_get_db
from core.database.CRUD import PGCreation, PGRetrieve
import csv
import tempfile
from fastapi.responses import FileResponse

router = APIRouter()

TokenDependencies = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]

@router.post(
    "/",
    description="Create log entry (with tenant ID)",
    response_model=LogEntryCreateResponse
)
async def get_log(
    payload: CreateLogPayload,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db),
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")

        status = await PGCreation(db).create_new_log(
            log=payload,
            tenant_id=token_data.get("tenant_id", None),
            user_id=token_data.get("user_id", None)
        )
        if not status:
            return LogEntryCreateResponse(message="Failed to create log!")
        return LogEntryCreateResponse(
            message="Create Log Successfully!",
            log=payload.model_dump()
        )
    except Exception:
        message = "Failed to create log!"
        logger.error(f"{message}: {traceback.format_exc()}")
        return LogEntryCreateResponse(message=message)
    

@router.get(
    "/",
    description="Search/filter logs (tenant-scoped)",
    response_model=GetLogsResponse
)
async def get_logs(
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")

        logs = await PGRetrieve(db).retrieve_logs(
            tenant_id=token_data.get("tenant_id", None)
        )

        if not logs:
            return GetLogsResponse(message="There is no logs available")

        return GetLogsResponse(
            message="Retrieve logs successfully!",
            logs=logs
        )
    except Exception:
        message = "Failed to get logs!"
        logger.error(f"{message}: {traceback.format_exc()}")
        return GetLogsResponse(message=message)

@router.get(
    "/export",
    description="Export logs (tenant-scoped)",
)
async def export_logs(
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")

        tenant_id = token_data.get("tenant_id")
        logs = await PGRetrieve(db).retrieve_logs(tenant_id=tenant_id)

        if not logs:
            raise HTTPException(status_code=404, detail="No logs found for export")

        with tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', dir='/tmp', suffix='.csv') as tmpfile:
            writer = csv.writer(tmpfile)
            writer.writerow(list(logs[0].model_dump().keys()))
            for log in logs:
                writer.writerow(log.model_dump().values())
            tmpfile.close()
            return FileResponse(tmpfile.name, filename="logs.csv", media_type="text/csv", headers={"Content-Disposition": "attachment; filename=logs.csv"})
        
    except Exception as e:
        message = f"Failed to export logs: {str(e)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

@router.get(
    "/{id}",
    description="Search/filter logs (tenant-scoped)",
    response_model=GetLogResponse
)
async def get_logs(
    id: str,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")

        log = await PGRetrieve(db).retrieve_logs(
            tenant_id=token_data.get("tenant_id", None),
            log_id=id,
            is_get_one=True
        )

        if not log:
            return GetLogResponse(message="There is no log available")

        return GetLogResponse(
            message="Retrieve logs successfully!",
            log=log
        )
    except Exception:
        message = "Failed to get logs!"
        logger.error(f"{message}: {traceback.format_exc()}")
        return GetLogResponse(message=message)
