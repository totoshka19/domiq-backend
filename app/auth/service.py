import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import RegisterRequest, UserUpdate
from core.security import hash_password, verify_password


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def register(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await get_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await get_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
    return user


async def update_me(db: AsyncSession, user: User, data: UserUpdate) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
