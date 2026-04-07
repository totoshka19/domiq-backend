import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.listings.models import DealType, ListingStatus, PropertyType


class ListingPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    order: int
    is_main: bool


class ListingCreate(BaseModel):
    title: str
    description: str = ""
    deal_type: DealType
    property_type: PropertyType
    price: Decimal
    currency: str = "RUB"
    area: Decimal
    rooms: Optional[int] = None
    floor: Optional[int] = None
    floors_total: Optional[int] = None
    address: str
    city: str
    district: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    area: Optional[Decimal] = None
    rooms: Optional[int] = None
    floor: Optional[int] = None
    floors_total: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    status: Optional[ListingStatus] = None


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str
    deal_type: DealType
    property_type: PropertyType
    price: Decimal
    currency: str
    area: Decimal
    rooms: Optional[int]
    floor: Optional[int]
    floors_total: Optional[int]
    address: str
    city: str
    district: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    status: ListingStatus
    is_moderated: bool
    reject_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    photos: list[ListingPhotoResponse] = []


class ListingsPage(BaseModel):
    items: list[ListingResponse]
    total: int
    page: int
    limit: int
    pages: int


class MapPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    latitude: Decimal
    longitude: Decimal
    price: Decimal


class ListingsMapResponse(BaseModel):
    points: list[MapPoint]
