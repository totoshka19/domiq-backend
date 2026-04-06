import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PhotoUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    url: str
    order: int
    is_main: bool


class PhotoReorderItem(BaseModel):
    photo_id: uuid.UUID
    order: int


class PhotoReorderRequest(BaseModel):
    photos: list[PhotoReorderItem]
