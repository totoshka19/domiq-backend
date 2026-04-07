from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

_FAKE_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _mock_s3():
    mock = MagicMock()
    mock.put_object.return_value = {}
    return mock


# ── PATCH /api/users/me/avatar ────────────────────────────────────────────────

async def test_upload_avatar_success(client: AsyncClient, user_token: str):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp = await client.patch(
            "/api/users/me/avatar",
            files={"file": ("avatar.png", BytesIO(_FAKE_PNG), "image/png")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["avatar_url"] is not None
    assert "avatar.png" not in data["avatar_url"]  # сохраняется по user_id, не оригинальному имени


async def test_upload_avatar_wrong_content_type(client: AsyncClient, user_token: str):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp = await client.patch(
            "/api/users/me/avatar",
            files={"file": ("avatar.gif", BytesIO(b"GIF89a"), "image/gif")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
    assert resp.status_code == 400


async def test_upload_avatar_unauthorized(client: AsyncClient):
    resp = await client.patch(
        "/api/users/me/avatar",
        files={"file": ("avatar.png", BytesIO(_FAKE_PNG), "image/png")},
    )
    assert resp.status_code == 401


async def test_upload_avatar_updates_existing(client: AsyncClient, user_token: str):
    """Повторная загрузка перезаписывает avatar_url."""
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp1 = await client.patch(
            "/api/users/me/avatar",
            files={"file": ("first.png", BytesIO(_FAKE_PNG), "image/png")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp2 = await client.patch(
            "/api/users/me/avatar",
            files={"file": ("second.png", BytesIO(_FAKE_PNG), "image/png")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    # Оба запроса обновляют один и тот же пользователь — avatar_url должен быть
    assert resp2.json()["avatar_url"] is not None
