from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.listings.models import DealType, PropertyType
from app.listings.schemas import ListingsPage
from app.search import service
from app.search.schemas import AutocompleteItem, AutocompleteResponse
from core.database import get_db

router = APIRouter()


@router.get("", response_model=ListingsPage)
async def search_listings(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
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
    db: AsyncSession = Depends(get_db),
) -> ListingsPage:
    return await service.search(
        db, q, page, limit,
        city, deal_type, property_type,
        price_min, price_max, rooms, area_min, area_max,
    )


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    q: str = Query(..., min_length=2, description="Начало названия города"),
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> AutocompleteResponse:
    items = await service.autocomplete(db, q, limit)
    return AutocompleteResponse(items=[AutocompleteItem(**i) for i in items])
