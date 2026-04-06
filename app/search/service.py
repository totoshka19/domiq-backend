import math
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.listings.models import DealType, Listing, ListingStatus, PropertyType
from app.listings.schemas import ListingsPage


async def search(
    db: AsyncSession,
    query: str,
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
) -> ListingsPage:
    # Строим tsvector по трём полям с весами:
    # title — A (самый высокий), address — B, description — C
    search_vector = func.to_tsvector(
        "russian",
        func.coalesce(Listing.title, "")
        + " "
        + func.coalesce(Listing.address, "")
        + " "
        + func.coalesce(Listing.description, ""),
    )
    search_query = func.plainto_tsquery("russian", query)
    rank = func.ts_rank(search_vector, search_query)

    base = (
        select(Listing)
        .options(selectinload(Listing.photos))
        .where(
            Listing.status == ListingStatus.active,
            search_vector.op("@@")(search_query),
        )
    )

    if city:
        base = base.where(Listing.city.ilike(f"%{city}%"))
    if deal_type:
        base = base.where(Listing.deal_type == deal_type)
    if property_type:
        base = base.where(Listing.property_type == property_type)
    if price_min is not None:
        base = base.where(Listing.price >= price_min)
    if price_max is not None:
        base = base.where(Listing.price <= price_max)
    if rooms is not None:
        base = base.where(Listing.rooms == rooms)
    if area_min is not None:
        base = base.where(Listing.area >= area_min)
    if area_max is not None:
        base = base.where(Listing.area <= area_max)

    count_result = await db.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base.order_by(rank.desc()).offset((page - 1) * limit).limit(limit)
    )
    items = list(result.scalars().all())

    return ListingsPage(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


async def autocomplete(db: AsyncSession, query: str, limit: int = 10) -> list[dict]:
    if not query or len(query) < 2:
        return []

    result = await db.execute(
        select(Listing.city, func.count(Listing.id).label("count"))
        .where(
            Listing.status == ListingStatus.active,
            Listing.city.ilike(f"%{query}%"),
        )
        .group_by(Listing.city)
        .order_by(func.count(Listing.id).desc())
        .limit(limit)
    )
    return [{"city": row.city, "count": row.count} for row in result.all()]
