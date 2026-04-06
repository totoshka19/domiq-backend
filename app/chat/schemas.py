import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    listing_id: uuid.UUID


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    text: str
    is_read: bool
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    created_at: datetime
    last_message: MessageResponse | None = None


class WsMessageIn(BaseModel):
    text: str


class WsMessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    text: str
    created_at: str
