import math
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.listings.models import DealType, Favorite, Listing, ListingStatus, PropertyType
from app.listings.schemas import ListingCreate, ListingUpdate, ListingsMapResponse, ListingsPage, MapPoint


async def get_by_id(db: AsyncSession, listing_id: uuid.UUID) -> Listing:
    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.photos), selectinload(Listing.owner))
        .where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return listing


async def get_by_id_for_user(
    db: AsyncSession, listing_id: uuid.UUID, user_id: Optional[uuid.UUID]
) -> Listing:
    listing = await get_by_id(db, listing_id)
    if user_id:
        fav = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.listing_id == listing_id,
            )
        )
        listing._is_favorite = fav.scalar_one_or_none() is not None
    else:
        listing._is_favorite = False
    return listing


async def get_list(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    city: Optional[str] = None,
    deal_type: Optional[DealType] = None,
    property_type: Optional[PropertyType] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    rooms: Optional[int] = None,
    area_min: Optional[float] = None,
    area_max: Optional[float] = None,
    floor_min: Optional[int] = None,
    floor_max: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> ListingsPage:
    query = (
        select(Listing)
        .options(selectinload(Listing.photos), selectinload(Listing.owner))
        .where(Listing.status == ListingStatus.active)
    )

    if city:
        query = query.where(Listing.city.ilike(f"%{city}%"))
    if deal_type:
        query = query.where(Listing.deal_type == deal_type)
    if property_type:
        query = query.where(Listing.property_type == property_type)
    if price_min is not None:
        query = query.where(Listing.price >= price_min)
    if price_max is not None:
        query = query.where(Listing.price <= price_max)
    if rooms is not None:
        query = query.where(Listing.rooms == rooms)
    if area_min is not None:
        query = query.where(Listing.area >= area_min)
    if area_max is not None:
        query = query.where(Listing.area <= area_max)
    if floor_min is not None:
        query = query.where(Listing.floor >= floor_min)
    if floor_max is not None:
        query = query.where(Listing.floor <= floor_max)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    sort_column = getattr(Listing, sort_by, Listing.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return ListingsPage(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


async def get_map_points(
    db: AsyncSession,
    city: Optional[str] = None,
    deal_type: Optional[DealType] = None,
    property_type: Optional[PropertyType] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
) -> ListingsMapResponse:
    query = (
        select(Listing)
        .where(
            Listing.status == ListingStatus.active,
            Listing.latitude.is_not(None),
            Listing.longitude.is_not(None),
        )
    )
    if city:
        query = query.where(Listing.city.ilike(f"%{city}%"))
    if deal_type:
        query = query.where(Listing.deal_type == deal_type)
    if property_type:
        query = query.where(Listing.property_type == property_type)
    if price_min is not None:
        query = query.where(Listing.price >= price_min)
    if price_max is not None:
        query = query.where(Listing.price <= price_max)

    result = await db.execute(query)
    points = [
        MapPoint(id=l.id, latitude=l.latitude, longitude=l.longitude, price=l.price)
        for l in result.scalars().all()
    ]
    return ListingsMapResponse(points=points)


async def create(db: AsyncSession, data: ListingCreate, owner_id: uuid.UUID) -> Listing:
    listing = Listing(owner_id=owner_id, **data.model_dump())
    db.add(listing)
    await db.commit()
    await db.refresh(listing, ["photos"])

    # Уведомляем администратора о новом объявлении на модерацию
    from core.config import settings
    if settings.ADMIN_EMAIL:
        from app.notifications.tasks import send_moderation_notification
        send_moderation_notification.delay(settings.ADMIN_EMAIL, listing.title)

    return listing


async def update(
    db: AsyncSession,
    listing_id: uuid.UUID,
    data: ListingUpdate,
    current_user_id: uuid.UUID,
    is_admin: bool = False,
) -> Listing:
    listing = await get_by_id(db, listing_id)
    if not is_admin and listing.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому объявлению")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)

    await db.commit()
    result = await db.execute(
        select(Listing).options(selectinload(Listing.photos), selectinload(Listing.owner)).where(Listing.id == listing_id)
    )
    return result.scalar_one()


async def archive(
    db: AsyncSession,
    listing_id: uuid.UUID,
    current_user_id: uuid.UUID,
    is_admin: bool = False,
) -> Listing:
    listing = await get_by_id(db, listing_id)
    if not is_admin and listing.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому объявлению")

    listing.status = ListingStatus.archived
    owner_id = listing.owner_id
    await db.commit()

    # Уведомляем владельца об изменении статуса
    from app.auth.models import User
    owner_result = await db.execute(select(User).where(User.id == owner_id))
    owner = owner_result.scalar_one_or_none()
    if owner:
        from app.notifications.tasks import send_listing_status_notification
        send_listing_status_notification.delay(owner.email, listing.title, ListingStatus.archived.value)

    result = await db.execute(
        select(Listing).options(selectinload(Listing.photos), selectinload(Listing.owner)).where(Listing.id == listing_id)
    )
    return result.scalar_one()


async def add_favorite(
    db: AsyncSession, listing_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await get_by_id(db, listing_id)

    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id, Favorite.listing_id == listing_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Уже в избранном")

    db.add(Favorite(user_id=user_id, listing_id=listing_id))
    await db.commit()


async def remove_favorite(
    db: AsyncSession, listing_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id, Favorite.listing_id == listing_id
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="Не найдено в избранном")
    await db.delete(fav)
    await db.commit()


async def get_favorites(
    db: AsyncSession, user_id: uuid.UUID, page: int = 1, limit: int = 20
) -> ListingsPage:
    query = (
        select(Listing)
        .options(selectinload(Listing.photos), selectinload(Listing.owner))
        .join(Favorite, Favorite.listing_id == Listing.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
    )
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    result = await db.execute(query.offset((page - 1) * limit).limit(limit))
    return ListingsPage(
        items=list(result.scalars().all()),
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


async def get_my(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
    status: Optional[ListingStatus] = None,
) -> ListingsPage:
    query = (
        select(Listing)
        .options(selectinload(Listing.photos), selectinload(Listing.owner))
        .where(Listing.owner_id == user_id)
    )
    if status is not None:
        query = query.where(Listing.status == status)
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    result = await db.execute(
        query.order_by(Listing.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    return ListingsPage(
        items=list(result.scalars().all()),
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


async def get_similar(
    db: AsyncSession,
    listing_id: uuid.UUID,
    limit: int = 6,
) -> list[Listing]:
    listing = await get_by_id(db, listing_id)

    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.photos), selectinload(Listing.owner))
        .where(
            Listing.id != listing_id,
            Listing.status == ListingStatus.active,
            Listing.city == listing.city,
            Listing.deal_type == listing.deal_type,
            Listing.property_type == listing.property_type,
        )
        .order_by(func.abs(Listing.price - listing.price))
        .limit(limit)
    )
    return list(result.scalars().all())
