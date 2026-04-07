import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import service
from app.admin.schemas import AdminListingResponse, AdminUserResponse, RejectRequest, StatsResponse
from app.auth.dependencies import role_required
from app.auth.models import User
from app.listings.models import ListingStatus
from core.database import get_db

router = APIRouter()

_admin = Depends(role_required("admin"))


@router.get("/users", response_model=dict)
async def get_users(
    page: int = 1,
    limit: int = Query(50, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    _: User = _admin,
    db: AsyncSession = Depends(get_db),
) -> dict:
    users, total = await service.get_users(db, page, limit, is_active, search)
    return {
        "items": users,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.patch("/users/{user_id}/block", response_model=AdminUserResponse)
async def block_user(
    user_id: uuid.UUID,
    _: User = _admin,
    db: AsyncSession = Depends(get_db),
) -> object:
    return await service.set_user_active(db, user_id, is_active=False)


@router.patch("/users/{user_id}/unblock", response_model=AdminUserResponse)
async def unblock_user(
    user_id: uuid.UUID,
    _: User = _admin,
    db: AsyncSession = Depends(get_db),
) -> object:
    return await service.set_user_active(db, user_id, is_active=True)


@router.get("/listings", response_model=dict)
async def get_listings(
    page: int = 1,
    limit: int = Query(50, le=100),
    status: Optional[ListingStatus] = None,
    is_moderated: Optional[bool] = None,
    search: Optional[str] = None,
    _: User = _admin,
    db: AsyncSession = Depends(get_db),
) -> dict:
    listings, total = await service.get_listings(db, page, limit, status, is_moderated, search)
    return {
        "items": [AdminListingResponse.model_validate(l) for l in listings],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.patch("/listings/{listing_id}/approve", response_model=AdminListingResponse)
async def approve_listing(
    listing_id: uuid.UUID,
    _: User = _admin,
    db: AsyncSession = Depends(get_db),
) -> object:
    return await service.moderate_listing(db, listing_id, approve=True)


@router.patch("/listings/{listing_id}/reject", response_model=AdminListingResponse)
async def reject_listing(
    listing_id: uuid.UUID,
    data: RejectRequest,
    _: User = _admin,
    db: AsyncSession = Depends(get_db),
) -> object:
    return await service.moderate_listing(db, listing_id, approve=False, reason=data.reason)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    _: User = _admin,
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    return await service.get_stats(db)
