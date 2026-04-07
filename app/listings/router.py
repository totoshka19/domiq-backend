import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, role_required
from app.auth.models import User, UserRole
from app.listings import service
from app.listings.models import DealType, ListingStatus, PropertyType
from app.listings.schemas import ListingCreate, ListingResponse, ListingsMapResponse, ListingsPage, ListingUpdate
from core.database import get_db

router = APIRouter()


@router.get("/favorites", response_model=list[ListingResponse])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    return await service.get_favorites(db, current_user.id)


@router.get("/my", response_model=list[ListingResponse])
async def get_my(
    status: Optional[ListingStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    return await service.get_my(db, current_user.id, status)


@router.get("", response_model=ListingsPage)
async def get_listings(
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
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
) -> ListingsPage:
    return await service.get_list(
        db, page, limit, city, deal_type, property_type,
        price_min, price_max, rooms, area_min, area_max,
        sort_by, sort_order,
    )


@router.get("/map", response_model=ListingsMapResponse)
async def get_map(
    city: Optional[str] = None,
    deal_type: Optional[DealType] = None,
    property_type: Optional[PropertyType] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
) -> ListingsMapResponse:
    return await service.get_map_points(db, city, deal_type, property_type, price_min, price_max)


@router.get("/{listing_id}/similar", response_model=list[ListingResponse])
async def get_similar(
    listing_id: uuid.UUID,
    limit: int = 6,
    db: AsyncSession = Depends(get_db),
) -> list:
    return await service.get_similar(db, listing_id, limit)


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    return await service.get_by_id(db, listing_id)


@router.post("", response_model=ListingResponse, status_code=201)
async def create_listing(
    data: ListingCreate,
    current_user: User = Depends(role_required("agent", "admin")),
    db: AsyncSession = Depends(get_db),
) -> object:
    return await service.create(db, data, current_user.id)


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: uuid.UUID,
    data: ListingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    return await service.update(
        db, listing_id, data,
        current_user.id,
        is_admin=(current_user.role == UserRole.admin),
    )


@router.delete("/{listing_id}", response_model=ListingResponse)
async def archive_listing(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    return await service.archive(
        db, listing_id,
        current_user.id,
        is_admin=(current_user.role == UserRole.admin),
    )


@router.post("/{listing_id}/favorite", status_code=204)
async def add_favorite(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.add_favorite(db, listing_id, current_user.id)


@router.delete("/{listing_id}/favorite", status_code=204)
async def remove_favorite(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.remove_favorite(db, listing_id, current_user.id)
