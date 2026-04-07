from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
)
from core.database import get_db
from core.redis import blacklist_token, is_token_blacklisted
from core.security import create_access_token, create_refresh_token, decode_token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    return await service.register(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await service.authenticate(db, data.email, data.password)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest) -> TokenResponse:
    try:
        payload = decode_token(data.refresh_token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Невалидный refresh токен")
    except JWTError:
        raise HTTPException(status_code=401, detail="Невалидный refresh токен")

    if await is_token_blacklisted(data.refresh_token):
        raise HTTPException(status_code=401, detail="Токен отозван, войдите снова")

    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: RefreshRequest) -> None:
    try:
        payload = decode_token(data.refresh_token)
        exp = payload.get("exp")
        ttl = max(int(exp - datetime.now(UTC).timestamp()), 1) if exp else 1
    except JWTError:
        ttl = 1

    await blacklist_token(data.refresh_token, ttl)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await service.update_me(db, current_user, data)
