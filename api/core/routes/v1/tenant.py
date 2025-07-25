from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_get_db
from core.services.authentication import AuthenService
from core.database.CRUD import PGRetrieve, PGCreation
from core.schemas.payloads.tenant import *
from core.schemas.v1.tenant import Tenant
from core.config import logger
import traceback
from core.limiter import RATE_LIMITER

router = APIRouter()
Limiter = RATE_LIMITER.get_limiter()

TokenDependencies = Annotated[
    HTTPAuthorizationCredentials, Depends(HTTPBearer())
]


@router.get("/", response_model=ListTenantsResponse)
@Limiter.limit(RATE_LIMITER.default_limit)
async def list_out_tenants(
    request: Request,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db),
):
    """Get the tenants information (based on Admin role only)

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

        if not AuthenService.is_admin_role(token_data.get("role", "")):
            raise HTTPException(
                status_code=401,
                detail="Role token is invalid and not allowed.",
            )

        tenants = await PGRetrieve(db).retrieve_tenants()

        if not tenants:
            return ListTenantsResponse(
                message="There is no tenants available!"
            )

        return ListTenantsResponse(
            message="Retrieve tenants successfully!", tenants=tenants
        )

    except HTTPException:
        raise
    except Exception:
        message = "Failed to retrieve tenants!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)


@router.post("/", response_model=CreateTenantResponse)
@Limiter.limit(RATE_LIMITER.default_limit)
async def create_tenant(
    payload: CreateTenantPayload,
    request: Request,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db),
):
    """Get the tenants information (based on Admin role only)

    Args:
        payload (CreateTenantPayload): information of new tenant need to create.
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

        if not AuthenService.is_admin_role(token_data.get("role", "")):
            raise HTTPException(
                status_code=401,
                detail="Role token is invalid and not allowed.",
            )

        new_tenant = Tenant(name=payload.tenant_name)
        _ = await PGCreation(db).create_new_tenant(new_tenant)

        return CreateTenantResponse(
            message="Create tenants successfully!",
            tenant=new_tenant.model_dump(),
        )

    except HTTPException:
        raise
    except Exception:
        message = "Failed to create tenant!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)
