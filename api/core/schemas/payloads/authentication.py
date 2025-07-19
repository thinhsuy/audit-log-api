from pydantic import BaseModel
from typing import Optional

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

class TenantUserCreatePayload(BaseModel):
    tenant_name: str
    username: str
    email: Optional[str] = None

class TenantUserCreateResponse(BaseModel):
    message: str
    tenant: Optional[dict] = None
    user: Optional[dict] = None
