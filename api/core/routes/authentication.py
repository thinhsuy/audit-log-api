from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.schemas.payloads.authentication import (
    CreateAccessTokenPayload,
    CreateAccessTokenResponse,
    TenantUserCreateResponse,
    CreateAccountPayload,
)
from core.services.authentication import AuthenService
from core.config import logger
from core.services.authentication import AuthenService
from core.schemas.v1.tenant import Tenant
from core.schemas.v1.user import User
from core.schemas.v1.session import Session
from datetime import datetime, timedelta
import traceback
from core.database.CRUD import PGRetrieve
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, VIETNAM_TZ
from core.database import async_get_db
from core.limiter import RATE_LIMITER

router = APIRouter()
Limiter = RATE_LIMITER.get_limiter()


@router.post(
    "/user-account",
    response_model=TenantUserCreateResponse,
    description="Create new tenant and user in that tenant",
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def create_user_associated_tenant(
    payload: CreateAccountPayload,
    request: Request,
    db: AsyncSession = Depends(async_get_db),
):
    """Create a new user account based on tenant

    Args:
        payload (CreateAccountPayload): request user and tenant information needs to createdS
        request (Request): HTTP request to checkup rate limit declaration
        db (AsyncSession, optional): sessionmaker for each connection request. Defaults to Depends(async_get_db).
    """
    try:
        tenant = Tenant(name=payload.tenant_name)

        if not tenant:
            raise HTTPException(status_code=401, detail="The tenant given is invalid!")

        user = User(
            username=payload.username,
            email=payload.email,
            tenant_id=tenant.id,
            role=payload.role,
        )
        response = await AuthenService.create_new_user_account(
            tenant=tenant, user=user, db=db
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
            user=user.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as ex:
        message = "Create new account failed!"
        logger.error(f"{message}. {traceback.format_exc()}")
        return TenantUserCreateResponse(message=message)


@router.get(
    "/access-token", response_model=CreateAccessTokenResponse
)
@Limiter.limit(RATE_LIMITER.default_limit)
async def generate_new_access_token(
    request: Request,
    user_id: str = Query(
        None, description="User Id to create session"
    ),
    expired_miniutes: int = Query(
        60, ge=1, description="Time expired of access token count from now"
    ),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Create new session to pg_db and then generate an access token
    """
    try:
        if not user_id:
            raise HTTPException(status_code=422, detail="User id cannot be empty")

        # extract the time of expiration
        time_now = datetime.now(VIETNAM_TZ)
        expired_miniutes = (
            expired_miniutes
            if expired_miniutes
            else ACCESS_TOKEN_EXPIRE_MINUTES
        )
        time_expired = time_now + timedelta(minutes=expired_miniutes)

        # prepare the token data based on tenant and user data
        user = await PGRetrieve(db).retrieve_user(
            user_id=user_id
        )

        if not user:
            raise HTTPException(status_code=422, detail="Cannot find user based on given id")
    
        tenant = await PGRetrieve(db).retrieve_tenant(
            tenant_id=user.tenant_id
        )

        if not tenant:
            raise HTTPException(
                status_code=422,
                detail="User have no tenant valid related!",
            )

        token_data = {}
        tenant_data = tenant.model_dump()
        user_data = user.model_dump()
        token_data.update(tenant_data)
        token_data.update({"tenant_id": tenant.id})
        token_data.update(user_data)
        token_data.update({"user_id": user.id})

        # generate access token
        access_token = AuthenService.create_access_token(
            data=token_data, time_expired=time_expired
        )

        # assign access token to new session
        session = Session(
            tenant_id=tenant.id,
            user_id=user.id,
            access_token=access_token,
            started_at=time_now,
            ended_at=time_expired,
        )

        new_session = await AuthenService.create_new_session_access(
            session=session, db=db
        )
        if not new_session:
            raise Exception("Create session failed!")

        return CreateAccessTokenResponse(
            message="Create access token successfully!",
            session=new_session.model_dump(),
        )

    except HTTPException:
        raise
    except Exception:
        message = (
            f"Failed to generate token for user {user_id}"
        )
        print(message, traceback.format_exc())
        logger.error(f"{message}: {traceback.format_exc()}")
        return CreateAccessTokenResponse(message=message)
