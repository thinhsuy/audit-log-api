from pydantic import BaseModel
from typing import List, Optional
from core.schemas.v1.tenant import Tenant


class ListTenantsResponse(BaseModel):
    message: str
    tenants: Optional[List[Tenant]] = None


class CreateTenantPayload(BaseModel):
    tenant_name: str


class CreateTenantResponse(BaseModel):
    message: str
    tenant: Optional[Tenant] = None
