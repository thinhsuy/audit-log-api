import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, VIETNAM_TZ
from fastapi import Header, HTTPException

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    time_now = datetime.now(VIETNAM_TZ)
    if expires_delta:
        expire = time_now + expires_delta
    else:
        expire = time_now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Invalid token: missing tenant_id.")
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

def refresh_access_token(
    refresh_token: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    try:
        # Decode & verify the incoming refresh token
        payload: dict = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Invalid token: missing tenant_id.")
        
        
        now = datetime.now(VIETNAM_TZ)
        if expires_delta:
            exp = now + expires_delta
        else:
            exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload.update({"exp": exp})
        
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")