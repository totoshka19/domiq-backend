import uuid
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.listings.models import Listing, ListingPhoto
from app.files.schemas import PhotoReorderRequest
from core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PHOTOS_PER_LISTING = 20


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY or None,
        aws_secret_access_key=settings.S3_SECRET_KEY or None,
        region_name="auto",
    )


async def _get_listing_for_owner(
    db: AsyncSession, listing_id: uuid.UUID, user_id: uuid.UUID, is_admin: bool
) -> Listing:
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if not is_admin and listing.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому объявлению")
    return listing


async def upload_photos(
    db: AsyncSession,
    listing_id: uuid.UUID,
    files: list[UploadFile],
    user_id: uuid.UUID,
    is_admin: bool = False,
) -> list[ListingPhoto]:
    listing = await _get_listing_for_owner(db, listing_id, user_id, is_admin)

    result = await db.execute(
        select(ListingPhoto).where(ListingPhoto.listing_id == listing_id)
    )
    existing_photos = result.scalars().all()

    if len(existing_photos) + len(files) > MAX_PHOTOS_PER_LISTING:
        raise HTTPException(
            status_code=400,
            detail=f"Максимум {MAX_PHOTOS_PER_LISTING} фото на объявление",
        )

    s3 = _s3_client()
    created: list[ListingPhoto] = []
    next_order = max((p.order for p in existing_photos), default=-1) + 1

    for file in files:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимый тип файла: {file.content_type}. Разрешены: jpeg, png, webp",
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Файл превышает 10 МБ")

        ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
        key = f"listings/{listing_id}/{uuid.uuid4()}.{ext}"

        try:
            s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key,
                Body=content,
                ContentType=file.content_type,
            )
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {e}")

        url = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{key}"
        is_main = len(existing_photos) == 0 and len(created) == 0

        photo = ListingPhoto(
            listing_id=listing_id,
            url=url,
            order=next_order,
            is_main=is_main,
        )
        db.add(photo)
        created.append(photo)
        next_order += 1

    await db.commit()
    for photo in created:
        await db.refresh(photo)
    return created


async def delete_photo(
    db: AsyncSession,
    photo_id: uuid.UUID,
    user_id: uuid.UUID,
    is_admin: bool = False,
) -> None:
    result = await db.execute(select(ListingPhoto).where(ListingPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Фото не найдено")

    await _get_listing_for_owner(db, photo.listing_id, user_id, is_admin)

    if settings.S3_BUCKET_NAME and settings.S3_ACCESS_KEY:
        try:
            key = photo.url.split(f"/{settings.S3_BUCKET_NAME}/", 1)[-1]
            _s3_client().delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        except ClientError:
            pass  # не блокируем удаление из БД если S3 недоступен

    was_main = photo.is_main
    await db.delete(photo)
    await db.flush()

    if was_main:
        next_result = await db.execute(
            select(ListingPhoto)
            .where(ListingPhoto.listing_id == photo.listing_id)
            .order_by(ListingPhoto.order.asc())
            .limit(1)
        )
        next_photo = next_result.scalar_one_or_none()
        if next_photo:
            next_photo.is_main = True

    await db.commit()


async def reorder_photos(
    db: AsyncSession,
    listing_id: uuid.UUID,
    data: PhotoReorderRequest,
    user_id: uuid.UUID,
    is_admin: bool = False,
) -> list[ListingPhoto]:
    await _get_listing_for_owner(db, listing_id, user_id, is_admin)

    photo_ids = [item.photo_id for item in data.photos]
    result = await db.execute(
        select(ListingPhoto).where(
            ListingPhoto.listing_id == listing_id,
            ListingPhoto.id.in_(photo_ids),
        )
    )
    photos = {p.id: p for p in result.scalars().all()}

    for item in data.photos:
        if item.photo_id in photos:
            photos[item.photo_id].order = item.order

    await db.commit()
    return list(photos.values())
