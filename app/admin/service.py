import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.models import Conversation, Message
from app.listings.models import Listing, ListingStatus
from app.admin.schemas import StatsResponse


async def get_users(
    db: AsyncSession,
    page: int = 1,
    limit: int = 50,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> tuple[list[User], int]:
    query = select(User)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    return list(result.scalars().all()), total


async def set_user_active(db: AsyncSession, user_id: uuid.UUID, is_active: bool) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    return user


async def get_listings(
    db: AsyncSession,
    page: int = 1,
    limit: int = 50,
    status: Optional[ListingStatus] = None,
    is_moderated: Optional[bool] = None,
    search: Optional[str] = None,
) -> tuple[list[Listing], int]:
    query = select(Listing)
    if status:
        query = query.where(Listing.status == status)
    if is_moderated is not None:
        query = query.where(Listing.is_moderated == is_moderated)
    if search:
        query = query.where(
            Listing.title.ilike(f"%{search}%") | Listing.city.ilike(f"%{search}%")
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(Listing.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    return list(result.scalars().all()), total


async def moderate_listing(
    db: AsyncSession, listing_id: uuid.UUID, approve: bool
) -> Listing:
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if approve:
        listing.is_moderated = True
        listing.status = ListingStatus.active
    else:
        listing.is_moderated = False
        listing.status = ListingStatus.archived

    await db.commit()
    await db.refresh(listing)

    # Уведомляем владельца о решении модератора
    from app.auth.models import User as UserModel
    owner_result = await db.execute(select(UserModel).where(UserModel.id == listing.owner_id))
    owner = owner_result.scalar_one_or_none()
    if owner:
        try:
            from app.notifications.tasks import send_listing_status_notification
            send_listing_status_notification.delay(owner.email, listing.title, listing.status.value)
        except Exception:
            pass  # Celery недоступен — не блокируем модерацию

    return listing


async def get_stats(db: AsyncSession) -> StatsResponse:
    users_total = (await db.execute(select(func.count(User.id)))).scalar_one()
    users_active = (
        await db.execute(select(func.count(User.id)).where(User.is_active == True))  # noqa: E712
    ).scalar_one()
    listings_total = (await db.execute(select(func.count(Listing.id)))).scalar_one()
    listings_active = (
        await db.execute(
            select(func.count(Listing.id)).where(Listing.status == ListingStatus.active)
        )
    ).scalar_one()
    listings_pending = (
        await db.execute(
            select(func.count(Listing.id)).where(
                Listing.is_moderated == False,  # noqa: E712
                Listing.status == ListingStatus.active,
            )
        )
    ).scalar_one()
    conversations_total = (
        await db.execute(select(func.count(Conversation.id)))
    ).scalar_one()
    messages_total = (await db.execute(select(func.count(Message.id)))).scalar_one()

    return StatsResponse(
        users_total=users_total,
        users_active=users_active,
        listings_total=listings_total,
        listings_active=listings_active,
        listings_pending_moderation=listings_pending,
        conversations_total=conversations_total,
        messages_total=messages_total,
    )
