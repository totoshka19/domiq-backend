import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.chat import service
from app.chat.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
    WsMessageOut,
)
from core.database import AsyncSessionLocal, get_db

router = APIRouter()


# ── WebSocket connection manager ──────────────────────────────────────────────

class ConnectionManager:
    def __init__(self) -> None:
        # conversation_id → список активных WebSocket
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, conversation_id: str) -> None:
        await ws.accept()
        self._connections.setdefault(conversation_id, []).append(ws)

    def disconnect(self, ws: WebSocket, conversation_id: str) -> None:
        conns = self._connections.get(conversation_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, conversation_id: str, payload: dict) -> None:
        for ws in list(self._connections.get(conversation_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(ws, conversation_id)


manager = ConnectionManager()


# ── REST endpoints ─────────────────────────────────────────────────────────────

@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def start_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    conv = await service.get_or_create_conversation(db, data.listing_id, current_user.id)
    return _to_response(conv)


@router.get("/conversations", response_model=list[ConversationResponse])
async def my_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    conversations = await service.get_my_conversations(db, current_user.id)
    return [_to_response(c) for c in conversations]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    return await service.get_messages(db, conversation_id, current_user.id, limit, before_id)


@router.post("/conversations/{conversation_id}/read", status_code=204)
async def mark_read(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.mark_read(db, conversation_id, current_user.id)


# ── WebSocket ──────────────────────────────────────────────────────────────────

@router.websocket("/ws/{conversation_id}")
async def chat_ws(
    ws: WebSocket,
    conversation_id: uuid.UUID,
    token: str = Query(..., description="JWT access token"),
) -> None:
    # Аутентификация через query-параметр (браузер не поддерживает заголовки в WS)
    from jose import JWTError
    from core.security import decode_token

    try:
        payload = decode_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        await ws.close(code=4001)
        return

    conv_id_str = str(conversation_id)

    async with AsyncSessionLocal() as db:
        try:
            await service._get_conversation_for_member(db, conversation_id, user_id)
        except Exception:
            await ws.close(code=4003)
            return

    await manager.connect(ws, conv_id_str)
    try:
        while True:
            data = await ws.receive_json()
            text = str(data.get("text", "")).strip()
            if not text:
                continue

            async with AsyncSessionLocal() as db:
                msg = await service.save_message(db, conversation_id, user_id, text)

            await manager.broadcast(conv_id_str, WsMessageOut(
                id=str(msg.id),
                conversation_id=conv_id_str,
                sender_id=str(user_id),
                text=msg.text,
                created_at=msg.created_at.isoformat(),
            ).model_dump())

    except WebSocketDisconnect:
        manager.disconnect(ws, conv_id_str)


# ── helpers ────────────────────────────────────────────────────────────────────

def _to_response(conv: object) -> ConversationResponse:
    last = getattr(conv, "_last_message", None)
    return ConversationResponse(
        id=conv.id,
        listing_id=conv.listing_id,
        buyer_id=conv.buyer_id,
        seller_id=conv.seller_id,
        created_at=conv.created_at,
        last_message=MessageResponse.model_validate(last) if last else None,
    )
