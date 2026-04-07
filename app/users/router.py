from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.schemas import UserResponse
from app.files import service as files_service
from core.database import get_db

router = APIRouter()


@router.patch("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    url = await files_service.upload_avatar(db, file, current_user.id)
    current_user.avatar_url = url
    await db.commit()
    await db.refresh(current_user)
    return current_user
