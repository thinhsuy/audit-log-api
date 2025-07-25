from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    BackgroundTasks,
    Query,
)
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
from core.limiter import RATE_LIMITER
from core.schemas.v1.enum import UserRoleEnum

router = APIRouter()
Limiter = RATE_LIMITER.get_limiter()

TokenDependencies = Annotated[
    HTTPAuthorizationCredentials, Depends(HTTPBearer())
]


@router.post(
    "/",
    description="Create log entry (with tenant ID)",
    response_model=LogEntryCreateResponse,
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def get_log(
    payload: CreateLogPayload,
    background_tasks: BackgroundTasks,
    request: Request,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db),
):
    """Generate a new log

    Args:
        background_tasks (BackgroundTasks): an async task to handle background task for this request.
        token (TokenDependencies): JWT request for short-time authentication access
        request (Request): HTTP request to checkup rate limit declaration
        db (AsyncSession, optional): sessionmaker for each connection request. Defaults to Depends(async_get_db).
    """
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )
        
        if token_data.get("role", "") == UserRoleEnum.AUDITOR:
            raise HTTPException(status_code=401, detail="User with AUDITOR role cannot have action of create log")

        log = await PGCreation(db).create_new_log(
            log=payload,
            tenant_id=token_data.get("tenant_id", None),
            user_id=token_data.get("user_id", None),
        )
        if not log:
            return LogEntryCreateResponse(
                message="Failed to create log!"
            )

        background_tasks.add_task(
            Audit_SQS.send_message,
            {
                "type": "logs.created",
                "tenant_id": token_data.get("tenant_id", None),
                **log.model_dump(),
            },
        )

        return LogEntryCreateResponse(
            message="Create Log Successfully!",
            log=payload.model_dump(),
        )
    except HTTPException:
        raise
    except Exception:
        message = "Failed to create log!"
        logger.error(f"{message}: {traceback.format_exc()}")
        return LogEntryCreateResponse(message=message)


@router.get(
    "/",
    description="Search/filter logs (tenant-scoped)",
    response_model=GetLogsResponse,
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def get_logs(
    token: TokenDependencies,
    request: Request,
    skip: int = Query(
        None, ge=0, description="Number of records to skip"
    ),
    limit: int = Query(
        None, ge=1, le=1000, description="Max records to return"
    ),
    db: AsyncSession = Depends(async_get_db),
):
    """Get the range of logs (Tenant-scoped)

    Args:
        token (TokenDependencies): JWT request for short-time authentication access
        request (Request): HTTP request to checkup rate limit declaration
        skip (int): Number of records to skip
        limit (int): Max records to return
        db (AsyncSession, optional): sessionmaker for each connection request. Defaults to Depends(async_get_db).
    """
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )

        logs = await PGRetrieve(db).retrieve_logs(
            tenant_id=token_data.get("tenant_id", None),
            skip=skip,
            limit=limit,
        )

        if not logs:
            return GetLogsResponse(
                message="There is no logs available"
            )

        return GetLogsResponse(
            message="Retrieve logs successfully!", logs=logs
        )
    except HTTPException:
        raise
    except Exception:
        message = "Failed to get logs!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)


@router.get(
    "/export",
    description="Export logs (tenant-scoped)",
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def export_logs(
    token: TokenDependencies,
    request: Request,
    db: AsyncSession = Depends(async_get_db),
):
    """Export data logs retrieved in format of CSV file (Tenant-scoped)

    Args:
        token (TokenDependencies): JWT request for short-time authentication access
        request (Request): HTTP request to checkup rate limit declaration
        db (AsyncSession, optional): sessionmaker for each connection request. Defaults to Depends(async_get_db).
    """
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )

        tenant_id = token_data.get("tenant_id")
        logs = await PGRetrieve(db).retrieve_logs(tenant_id=tenant_id)

        if not logs:
            raise HTTPException(
                status_code=404, detail="No logs found for export"
            )

        with tempfile.NamedTemporaryFile(
            delete=False,
            mode="w",
            newline="",
            dir="/tmp",
            suffix=".csv",
        ) as tmpfile:
            writer = csv.writer(tmpfile)
            writer.writerow(list(logs[0].model_dump().keys()))
            for log in logs:
                writer.writerow(log.model_dump().values())
            tmpfile.close()
            return FileResponse(
                tmpfile.name,
                filename="logs.csv",
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=logs.csv"
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        message = f"Failed to export logs: {str(e)}"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)


@router.post(
    "/bulk",
    description="Bulk log creation (with tenant ID)",
    response_model=BulkLogCreateResponse,
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def bulk_create_logs(
    payload: List[CreateLogPayload],
    background_tasks: BackgroundTasks,
    request: Request,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db),
):
    """Create bulk of logs on the fly (Tenant-scoped)

    Args:
        background_tasks (BackgroundTasks): an async task to handle background task for this request.
        token (TokenDependencies): JWT request for short-time authentication access
        request (Request): HTTP request to checkup rate limit declaration
        db (AsyncSession, optional): sessionmaker for each connection request. Defaults to Depends(async_get_db).
    """
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )

        tenant_id = token_data.get("tenant_id", None)
        user_id = token_data.get("user_id", None)
        user_role = token_data.get("user_role", None)

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant id is invalid")

        if user_role and user_role == UserRoleEnum.AUDITOR:
            raise HTTPException(status_code=401, detail="User with AUDITOR role cannot have action of create bulk")

        logs: List[AuditLog] = await PGCreation(db).create_bulk_logs(
            logs=payload, tenant_id=tenant_id, user_id=user_id
        )
        if not logs:
            raise HTTPException(
                status_code=500, detail="Failed to create bulk logs"
            )

        background_tasks.add_task(
            Audit_SQS.send_message,
            {
                "type": "logs.created",
                "tenant_id": token_data.get("tenant_id", None),
                "logs": [log.model_dump() for log in logs],
            },
        )
        return BulkLogCreateResponse(
            message="Logs created successfully!",
            logs=[log.model_dump() for log in logs],
        )
    except HTTPException:
        raise
    except Exception:
        message = "Failed to create logs!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)


@router.delete(
    "/cleanup",
    description="Cleanup old logs (tenant-scoped)",
    response_model=CleanupLogResponse,
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def cleanup_old_logs(
    token: TokenDependencies,
    request: Request,
    db: AsyncSession = Depends(async_get_db),
):
    """Clean up retention logs api (Tenant-scoped)

    Args:
        token (TokenDependencies): JWT request for short-time authentication access
        request (Request): HTTP request to checkup rate limit declaration
        db (AsyncSession, optional): sessionmaker for each connection request. Defaults to Depends(async_get_db).
    """
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )

        tenant_id = token_data.get("tenant_id", None)
        user_role = token_data.get("user_role", None)

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant id is invalid")

        if user_role and user_role == UserRoleEnum.AUDITOR:
            raise HTTPException(status_code=401, detail="User with AUDITOR role cannot have action on delete logs")

        deleted_count = await PGDeletion(db).cleanup_old_logs(
            tenant_id
        )

        return CleanupLogResponse(
            message=f"Cleanup completed successfully! {deleted_count} logs deleted.",
            deleted_count=deleted_count,
        )
    except Exception:
        message = "Failed to cleanup old logs!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)


@router.get(
    "/stats",
    description="Get log statistics (tenant-scoped)",
    response_model=GetLogsStatsResponse,
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def get_logs_stats(
    token: TokenDependencies,
    request: Request,
    db: AsyncSession = Depends(async_get_db),
):
    """Generate statstistic data for logs assume (Tenant-scoped)

    Args:
        token (TokenDependencies): JWT request for short-time authentication access
        request (Request): HTTP request to checkup rate limit declaration
        db (AsyncSession, optional): sessionmaker for each connection request. Defaults to Depends(async_get_db).
    """
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )

        tenant_id = token_data.get("tenant_id", None)

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant id is invalid")

        stats = await PGRetrieve(db).get_logs_stats_by_tenant(
            tenant_id
        )

        return GetLogsStatsResponse(
            message="Log statistics retrieved successfully!",
            response=stats,
        )
    except HTTPException:
        raise
    except Exception:
        message = "Failed to get log statistics!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)


@router.get(
    "/{id}",
    description="Search/filter logs (tenant-scoped)",
    response_model=GetLogsResponse,
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def get_logs(
    id: str,
    token: TokenDependencies,
    request: Request,
    db: AsyncSession = Depends(async_get_db),
):
    """Get the range of logs by given id (Tenant-scoped)

    Args:
        token (TokenDependencies): JWT request for short-time authentication access
        request (Request): HTTP request to checkup rate limit declaration
        skip (int): Number of records to skip
        limit (int): Max records to return
        db (AsyncSession, optional): sessionmaker for each connection request. Defaults to Depends(async_get_db).
    """
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )
        tenant_id = token_data.get("tenant_id", None)

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant id is invalid")

        logs = await PGRetrieve(db).retrieve_logs(
            tenant_id=token_data.get("tenant_id", None),
            log_id=id,
        )
        if not logs:
            return GetLogsResponse(
                message="There is no logs available"
            )

        return GetLogsResponse(
            message="Retrieve logs successfully!", logs=logs
        )
    except HTTPException:
        raise
    except Exception:
        message = "Failed to get logs!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)
