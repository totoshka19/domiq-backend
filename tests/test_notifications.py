import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── Celery tasks ──────────────────────────────────────────────────────────────

def test_send_new_message_notification_no_smtp():
    """Без SMTP задача не падает — просто логирует."""
    from app.notifications.tasks import send_new_message_notification
    send_new_message_notification.apply(
        args=["recipient@test.com", "Иван", "Привет, квартира ещё доступна?"]
    )


def test_send_listing_status_notification_active():
    """Статус active — задача не падает."""
    from app.notifications.tasks import send_listing_status_notification
    send_listing_status_notification.apply(
        args=["owner@test.com", "Квартира в центре", "active"]
    )


def test_send_listing_status_notification_archived():
    """Статус archived — задача не падает."""
    from app.notifications.tasks import send_listing_status_notification
    send_listing_status_notification.apply(
        args=["owner@test.com", "Квартира в центре", "archived"]
    )


def test_send_moderation_notification():
    """Уведомление администратору о новом объявлении не падает."""
    from app.notifications.tasks import send_moderation_notification
    send_moderation_notification.apply(
        args=["admin@test.com", "Студия у метро"]
    )


def test_send_new_message_notification_calls_send_email():
    """Задача вызывает _send_email с правильными аргументами."""
    from app.notifications import tasks
    with patch.object(tasks, "_send_email") as mock_email:
        tasks.send_new_message_notification.apply(
            args=["r@test.com", "Мария", "Здравствуйте!"]
        )
        mock_email.assert_called_once()
        to_arg = mock_email.call_args.kwargs.get("to") or mock_email.call_args.args[0]
        assert to_arg == "r@test.com"


def test_send_listing_status_notification_unknown_status():
    """Неизвестный статус — не падает, использует raw значение."""
    from app.notifications.tasks import send_listing_status_notification
    send_listing_status_notification.apply(
        args=["owner@test.com", "Дом", "unknown_status"]
    )


def test_send_new_message_notification_long_text():
    """Длинный текст обрезается до 200 символов."""
    from app.notifications import tasks
    long_text = "А" * 300
    with patch.object(tasks, "_send_email") as mock_email:
        tasks.send_new_message_notification.apply(
            args=["r@test.com", "Иван", long_text]
        )
        body = mock_email.call_args.kwargs.get("body") or mock_email.call_args.args[2]
        assert "..." in body


# ── NotificationManager (unit) ────────────────────────────────────────────────

async def test_notification_manager_send_no_connections():
    """Отправка без подключённых клиентов не падает."""
    import uuid
    from app.notifications.router import NotificationManager
    manager = NotificationManager()
    await manager.send(uuid.uuid4(), {"type": "test"})


async def test_notification_manager_send_to_connected():
    """Менеджер отправляет сообщение подключённому WebSocket."""
    import uuid
    from app.notifications.router import NotificationManager
    from unittest.mock import AsyncMock, MagicMock

    manager = NotificationManager()
    user_id = uuid.uuid4()

    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock()
    manager._connections[str(user_id)] = [mock_ws]

    payload = {"type": "listing_status_changed", "status": "active"}
    await manager.send(user_id, payload)

    mock_ws.send_json.assert_awaited_once_with(payload)


async def test_notification_manager_disconnect_on_error():
    """При ошибке отправки WebSocket удаляется из connections."""
    import uuid
    from app.notifications.router import NotificationManager
    from unittest.mock import AsyncMock, MagicMock

    manager = NotificationManager()
    user_id = uuid.uuid4()

    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock(side_effect=Exception("connection closed"))
    manager._connections[str(user_id)] = [mock_ws]

    await manager.send(user_id, {"type": "test"})

    assert mock_ws not in manager._connections.get(str(user_id), [])


async def test_notification_manager_connect_disconnect():
    """connect добавляет, disconnect удаляет WebSocket."""
    import uuid
    from app.notifications.router import NotificationManager
    from unittest.mock import AsyncMock, MagicMock

    manager = NotificationManager()
    user_id = str(uuid.uuid4())

    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()

    await manager.connect(mock_ws, user_id)
    assert mock_ws in manager._connections[user_id]

    manager.disconnect(mock_ws, user_id)
    assert mock_ws not in manager._connections.get(user_id, [])
