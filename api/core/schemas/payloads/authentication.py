from pydantic import BaseModel
from typing import Optional
from core.schemas.v1.enum import UserRoleEnum


class CreateAccessTokenPayload(BaseModel):
    username: str
    tenant_name: str
    expired_miniutes: Optional[int] = None


class CreateAccessTokenResponse(BaseModel):
    message: str
    access_token: Optional[str] = None
    session: Optional[dict] = None


class RefreshTokenPayload(BaseModel):
    access_token: str


class CreateAccountPayload(BaseModel):
    tenant_name: str
    username: str
    role: UserRoleEnum = None
    email: Optional[str] = None


class TenantUserCreateResponse(BaseModel):
    message: str
    tenant: Optional[dict] = None
    user: Optional[dict] = None
