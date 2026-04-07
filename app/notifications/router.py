import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class NotificationManager:
    def __init__(self) -> None:
        # user_id (str) → список активных WebSocket
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, user_id: str) -> None:
        await ws.accept()
        self._connections.setdefault(user_id, []).append(ws)

    def disconnect(self, ws: WebSocket, user_id: str) -> None:
        conns = self._connections.get(user_id, [])
        if ws in conns:
            conns.remove(ws)

    async def send(self, user_id: uuid.UUID, payload: dict) -> None:
        for ws in list(self._connections.get(str(user_id), [])):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(ws, str(user_id))


notification_manager = NotificationManager()


@router.websocket("/ws")
async def notifications_ws(
    ws: WebSocket,
    token: str,
) -> None:
    from jose import JWTError
    from core.security import decode_token

    try:
        payload = decode_token(token)
        user_id = str(uuid.UUID(payload["sub"]))
    except (JWTError, KeyError, ValueError):
        await ws.close(code=4001)
        return

    await notification_manager.connect(ws, user_id)
    try:
        while True:
            await ws.receive_text()  # держим соединение открытым
    except WebSocketDisconnect:
        notification_manager.disconnect(ws, user_id)
