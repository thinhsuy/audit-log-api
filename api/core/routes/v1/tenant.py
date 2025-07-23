from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter()

TokenDependencies = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]

@router.get(
    "/",
    response_model=ListTenantsResponse
)
async def list_out_tenants(
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
        if not AuthenService.is_admin_role(token_data.get("role", "")):
            raise HTTPException(status_code=401, detail="Role token is invalid and not allowed.")

        tenants = await PGRetrieve(db).retrieve_tenants()

        if not tenants:
            return ListTenantsResponse(message="There is no tenants available!")

        return ListTenantsResponse(
            message="Retrieve tenants successfully!",
            tenants=tenants
        )
    except Exception:
        message = "Failed to retrieve tenants!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)

@router.post(
    "/",
    response_model=CreateTenantResponse
)
async def create_tenant(
    payload: CreateTenantPayload,
    token: TokenDependencies,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        token_data = AuthenService.verify_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")

        if not AuthenService.is_admin_role(token_data.get("role", "")):
            raise HTTPException(status_code=401, detail="Role token is invalid and not allowed.")

        new_tenant = Tenant(name=payload.tenant_name)
        _ = await PGCreation(db).create_new_tenant(new_tenant)

        return CreateTenantResponse(
            message="Create tenants successfully!",
            tenant=new_tenant.model_dump()
        )
    except Exception:
        message = "Failed to create tenant!"
        logger.error(f"{message}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=message)