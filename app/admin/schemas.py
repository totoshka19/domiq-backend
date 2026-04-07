import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.auth.models import UserRole
from app.listings.models import ListingStatus


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class RejectRequest(BaseModel):
    reason: str


class AdminListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    city: str
    status: ListingStatus
    is_moderated: bool
    reject_reason: Optional[str]
    created_at: datetime


class StatsResponse(BaseModel):
    users_total: int
    users_active: int
    listings_total: int
    listings_active: int
    listings_pending_moderation: int
    conversations_total: int
    messages_total: int
