import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from jose import JWTError
from core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    VIETNAM_TZ,
)
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.CRUD import PGRetrieve, PGCreation
from core.schemas.v1.tenant import Tenant
from core.schemas.v1.user import User
from core.schemas.v1.session import Session
from core.schemas.v1.enum import UserRoleEnum


class AuthenService:
    @staticmethod
    def create_access_token(
        data: dict, time_expired: Optional[datetime] = None
    ) -> str:
        """Encode a JWT token based on user_id and tenant_id -> update expired date"""
        data.update({"exp": time_expired})
        encoded_jwt = jwt.encode(
            data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(
                token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid token: missing tenant_id.",
                )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            )

    @staticmethod
    def refresh_access_token(
        refresh_token: str, expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Decode a new token JWT with new expire date"""
        try:
            payload: dict = jwt.decode(
                refresh_token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
            )
            now = datetime.now(VIETNAM_TZ)
            expire = now + (
                expires_delta
                or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            payload.update({"exp": expire})
            new_token = jwt.encode(
                payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
            )
            return new_token, payload

        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token.",
            )

    @staticmethod
    async def create_new_tenant_and_user(
        tenant: Tenant, user: User, db: AsyncSession
    ) -> dict:
        existed_tenant = await PGRetrieve(db).retrieve_tenant(
            tenant_name=tenant.name
        )
        if not existed_tenant:
            new_tenant = await PGCreation(db).create_new_tenant(tenant)
            if not tenant:
                return {
                    "status": False,
                    "message": f"There an error when create new tenant",
                }
            tenant = new_tenant
        else:
            tenant = existed_tenant

        # update user tenant_id with existed tenant
        user.tenant_id = tenant.id

        if await PGRetrieve(db).retrieve_user(username=user.username):
            return {
                "status": False,
                "message": f"This user already existed",
                "user": user.model_dump(),
                "tenant": tenant.model_dump(),
            }
        if not await PGCreation(db).create_new_user(user):
            return {
                "status": False,
                "message": f"There an error when create new user",
            }
        return {
            "status": True,
            "message": f"Create new user and tenant successfully!",
        }

    @staticmethod
    async def create_new_session_access(
        session: Session, db: AsyncSession
    ) -> Session:
        return await PGCreation(db).create_new_session(session)

    @staticmethod
    async def is_admin_role(role: str) -> bool:
        return role == UserRoleEnum.ADMIN
