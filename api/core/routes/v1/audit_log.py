from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from core.schemas.payloads.logs import *
from core.services.authentication import AuthenService
from core.config import logger
import traceback
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_get_db
from core.database.CRUD import PGCreation, PGRetrieve, PGDeletion
import csv
from typing import List
import tempfile
from fastapi.responses import FileResponse
from core.services import Audit_SQS

router = APIRouter()

TokenDependencies = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]

@router.post(
    "/",
    description="Create log entry (with tenant ID)",
    response_model=LogEntryCreateResponse
)
async def get_log(
    payload: CreateLogPayload,
    background_tasks: BackgroundTasks,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db),
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")

        log = await PGCreation(db).create_new_log(
            log=payload,
            tenant_id=token_data.get("tenant_id", None),
            user_id=token_data.get("user_id", None)
        )
        if not log:
            return LogEntryCreateResponse(message="Failed to create log!")
        
        background_tasks.add_task(
            Audit_SQS.send_message,
            {
                "type": "logs.created",
                **log.model_dump()
            }
        )

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

@router.post(
    "/bulk",
    description="Bulk log creation (with tenant ID)",
    response_model=BulkLogCreateResponse
)
async def bulk_create_logs(
    payload: List[CreateLogPayload],
    background_tasks: BackgroundTasks,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        
        tenant_id = token_data.get("tenant_id", None)
        user_id = token_data.get("user_id", None)

        logs: List[AuditLog] = await PGCreation(db).create_bulk_logs(
            logs=payload,
            tenant_id=tenant_id,
            user_id=user_id
        )
        if not logs:
            raise HTTPException(status_code=500, detail="Failed to create bulk logs")

        background_tasks.add_task(
            Audit_SQS.send_message,
            {
                "type": "logs.created",
                "logs": [
                    log.model_dump()
                    for log in logs
                ]
            }
        )
        return BulkLogCreateResponse(
            message="Logs created successfully!",
            logs=[log.model_dump() for log in logs]
        )
    except Exception:
        message = "Failed to create logs!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)

@router.delete(
    "/cleanup",
    description="Cleanup old logs (tenant-scoped)",
    response_model=CleanupLogResponse
)
async def cleanup_old_logs(
    token: TokenDependencies,
    retention_days: int = 90,
    db: AsyncSession = Depends(async_get_db),
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        
        tenant_id = token_data.get("tenant_id", None)
        deleted_count = await PGDeletion(db).cleanup_old_logs(tenant_id)

        return CleanupLogResponse(
            message=f"Cleanup completed successfully! {deleted_count} logs deleted.",
            deleted_count=deleted_count
        )
    except Exception:
        message = "Failed to cleanup old logs!"
        logger.error(f"{message}: {traceback.format_exc()}")
        return CleanupLogResponse(message=message)

@router.get(
    "/stats",
    description="Get log statistics (tenant-scoped)",
    response_model=GetLogsStatsResponse
)
async def get_logs_stats(
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        
        tenant_id = token_data.get("tenant_id", None)

        stats = await PGRetrieve(db).get_logs_stats_by_tenant(tenant_id)

        return GetLogsStatsResponse(
            message="Log statistics retrieved successfully!",
            response=stats
        )
    except Exception:
        message = "Failed to get log statistics!"
        logger.error(f"{message}: {traceback.format_exc()}")
        return GetLogsStatsResponse(message=message)

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
            return GetLogResponse(message=f"There is no log with id: {id}")

        return GetLogResponse(
            message="Retrieve log successfully!",
            log=log
        )
    except Exception as e:
        logger.error(f"Failed to get logs by id: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to get logs")
