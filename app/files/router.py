import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User, UserRole
from app.files import service
from app.files.schemas import PhotoReorderRequest, PhotoUploadResponse
from core.database import get_db

router = APIRouter()


@router.post("/upload", response_model=list[PhotoUploadResponse], status_code=201)
async def upload_photos(
    listing_id: uuid.UUID = Query(..., description="ID объявления"),
    files: list[UploadFile] = File(..., description="Фото (jpeg/png/webp, до 10 МБ каждое)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    return await service.upload_photos(
        db,
        listing_id,
        files,
        current_user.id,
        is_admin=(current_user.role == UserRole.admin),
    )


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.delete_photo(
        db,
        photo_id,
        current_user.id,
        is_admin=(current_user.role == UserRole.admin),
    )


@router.patch("/reorder", response_model=list[PhotoUploadResponse])
async def reorder_photos(
    listing_id: uuid.UUID = Query(..., description="ID объявления"),
    data: PhotoReorderRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    return await service.reorder_photos(
        db,
        listing_id,
        data,
        current_user.id,
        is_admin=(current_user.role == UserRole.admin),
    )
