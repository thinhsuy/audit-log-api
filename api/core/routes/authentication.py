from fastapi import APIRouter, HTTPException
from core.models import CreateAccessTokenPayload, CreateAccessTokenResponse, RefreshTokenPayload
from core.security.access_token import create_access_token, refresh_access_token
from core.config import logger

router = APIRouter()

@router.post(
    "/create-access-token",
    response_model=CreateAccessTokenResponse
)
def generate_new_access_token(payload: CreateAccessTokenPayload):
    try:
        access_token: str = create_access_token(
            data={
                "sub": payload.subject,
                "tenant_id": payload.tenant_id,
            }
        )
        return CreateAccessTokenResponse(access_token=access_token)
    except Exception as e:
        logger.error(f"Failed to generate tokens for user {payload.subject}")
        raise HTTPException(status_code=500, detail="Failed to generate tokens.")

@router.post(
    "/refresh-token",
    response_model=CreateAccessTokenResponse
)
async def refresh_token(payload: RefreshTokenPayload):
    """
    Refresh an expired access token using a valid refresh token.
    """
    try:
        new_access_token = refresh_access_token(refresh_token=payload.access_token)
        return CreateAccessTokenResponse(access_token=new_access_token)
    except Exception as e:
        logger.error(f"Failed to refresh tokens")
        raise HTTPException(status_code=500, detail="Failed to refresh tokens.")
        