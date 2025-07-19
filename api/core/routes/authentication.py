from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.schemas.payloads.authentication import (
    CreateAccessTokenPayload,
    CreateAccessTokenResponse,
    RefreshTokenPayload,
    TenantUserCreateResponse,
    TenantUserCreatePayload
)
from core.services.authentication import AuthenService
from core.config import logger
from core.database.base import async_get_db
from core.services.authentication import AuthenService
from core.schemas.v1.tenant import Tenant
from core.schemas.v1.user import User
from core.schemas.v1.session import Session
from datetime import datetime, timedelta
import traceback
from core.database.CRUD import PGRetrieve
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, VIETNAM_TZ

router = APIRouter()

@router.post(
    "/create-account",
    response_model=TenantUserCreateResponse,
    description="Create new tenant and user in that tenant"
)
async def create_tenant_and_user(
    payload: TenantUserCreatePayload,
    db: AsyncSession = Depends(async_get_db)
):
    try:
        tenant = Tenant(name=payload.tenant_name)
        user = User(
            username=payload.username,
            email=payload.email,
            tenant_id=tenant.id
        )
        response = await AuthenService.create_new_tenant_and_user(
            tenant=tenant,
            user=user,
            db=db
        )
        if not response.get("status", False):
            return TenantUserCreateResponse(
                message=response.get("message", None),
                tenant=response.get("tenant", None),
                user=response.get("user", None),
            )
        
        return TenantUserCreateResponse(
            message="Create new account successfully!",
            tenant=tenant.model_dump(),
            user=user.model_dump()
        )
    except Exception as ex:
        message="Create new account failed!"
        logger.error(f"{message}. {traceback.format_exc()}")
        return TenantUserCreateResponse(message=message)

@router.post(
    "/create-access-token",
    response_model=CreateAccessTokenResponse
)
async def generate_new_access_token(
    payload: CreateAccessTokenPayload,
    db: AsyncSession = Depends(async_get_db)
):
    """
    Create new session to pg_db and then generate an access token
    """
    try:
        # extract the time of expiration
        time_now = datetime.now(VIETNAM_TZ)
        expired_miniutes = payload.expired_miniutes if payload.expired_miniutes else ACCESS_TOKEN_EXPIRE_MINUTES
        time_expired = time_now + timedelta(minutes=expired_miniutes)

        # prepare the token data based on tenant and user data
        tenant = await PGRetrieve(db).retrieve_tenant(tenant_name=payload.tenant_name)
        user = await PGRetrieve(db).retrieve_user(username=payload.username)

        token_data = {}
        tenant_data = tenant.model_dump()
        user_data = user.model_dump()
        token_data.update(tenant_data)
        token_data.update({"tenant_id": tenant.id})
        token_data.update(user_data)
        token_data.update({"user_id": user.id})

        # generate access token
        access_token = AuthenService.create_access_token(
            data=token_data,
            time_expired=time_expired
        )

        # assign access token to new session
        session = Session(
            tenant_id=tenant.id,
            user_id=user.id,
            access_token=access_token,
            started_at=time_now,
            ended_at=time_expired
        )

        new_session = await AuthenService.create_new_session_access(session=session, db=db)
        if not new_session:
            raise Exception("Create session failed!")

        return CreateAccessTokenResponse(
            message="Create access token successfully!",
            access_token=access_token,
            session=new_session.model_dump()
        )
    except Exception:
        message = f"Failed to generate token for user {payload.user_id}"
        logger.error(f"{message}: {traceback.format_exc()}")
        return CreateAccessTokenResponse(message=message)

# @router.post(
#     "/refresh-token",
#     response_model=CreateAccessTokenResponse
# )
# async def refresh_token(payload: RefreshTokenPayload):
#     try:
#         new_access_token, _ = AuthenService.refresh_access_token(refresh_token=payload.access_token)

#         return CreateAccessTokenResponse(
#             message="Refresh access token successfully!",
#             access_token=new_access_token
#         )
#     except Exception as e:
#         message="Refresh access token failed!"
#         logger.error(f"{message}. {traceback.format_exc()}")
#         return CreateAccessTokenResponse(message)
