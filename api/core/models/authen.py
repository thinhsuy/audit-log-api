from pydantic import BaseModel
from typing import Optional

class CreateAccessTokenPayload(BaseModel):
    subject: str
    tenant_id: str

class CreateAccessTokenResponse(BaseModel):
    access_token: str

class RefreshTokenPayload(BaseModel):
    access_token: str