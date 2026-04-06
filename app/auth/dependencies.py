from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from core.database import get_db
from core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Невалидный токен")
    except JWTError:
        raise HTTPException(status_code=401, detail="Невалидный токен")

    from app.auth.service import get_by_id
    import uuid
    user = await get_by_id(db, uuid.UUID(user_id))
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
    return user


def role_required(*roles: str):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current_user
    return checker
