import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator

from app.listings.models import DealType, ListingStatus, PropertyType


class OwnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    avatar_url: Optional[str]
    role: str


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
    owner: Optional[OwnerResponse] = None
    main_photo_url: Optional[str] = None

    @model_validator(mode="after")
    def set_main_photo_url(self) -> "ListingResponse":
        main = next((p for p in self.photos if p.is_main), None)
        if main is None and self.photos:
            main = self.photos[0]
        self.main_photo_url = main.url if main else None
        return self


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
