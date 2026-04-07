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
    """Возвращает мок S3 клиента для патчинга."""
    mock = MagicMock()
    mock.put_object.return_value = {}
    mock.delete_object.return_value = {}
    return mock


# ── POST /api/files/upload ────────────────────────────────────────────────────

async def test_upload_photo_success(
    client: AsyncClient, listing: dict, agent_token: str
):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp = await client.post(
            f"/api/files/upload?listing_id={listing['id']}",
            files={"files": ("test.png", BytesIO(_FAKE_PNG), "image/png")},
            headers={"Authorization": f"Bearer {agent_token}"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 1
    assert data[0]["listing_id"] == listing["id"]
    assert data[0]["is_main"] is True
    assert "url" in data[0]


async def test_upload_multiple_photos(
    client: AsyncClient, listing: dict, agent_token: str
):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp = await client.post(
            f"/api/files/upload?listing_id={listing['id']}",
            files=[
                ("files", ("photo1.png", BytesIO(_FAKE_PNG), "image/png")),
                ("files", ("photo2.png", BytesIO(_FAKE_PNG), "image/png")),
            ],
            headers={"Authorization": f"Bearer {agent_token}"},
        )
    assert resp.status_code == 201
    assert len(resp.json()) == 2


async def test_upload_photo_wrong_content_type(
    client: AsyncClient, listing: dict, agent_token: str
):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp = await client.post(
            f"/api/files/upload?listing_id={listing['id']}",
            files={"files": ("test.gif", BytesIO(b"GIF89a"), "image/gif")},
            headers={"Authorization": f"Bearer {agent_token}"},
        )
    assert resp.status_code == 400


async def test_upload_photo_unauthorized(client: AsyncClient, listing: dict):
    resp = await client.post(
        f"/api/files/upload?listing_id={listing['id']}",
        files={"files": ("test.png", BytesIO(_FAKE_PNG), "image/png")},
    )
    assert resp.status_code == 401


async def test_upload_photo_forbidden_other_user(
    client: AsyncClient, listing: dict, user_token: str
):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp = await client.post(
            f"/api/files/upload?listing_id={listing['id']}",
            files={"files": ("test.png", BytesIO(_FAKE_PNG), "image/png")},
            headers={"Authorization": f"Bearer {user_token}"},
        )
    assert resp.status_code == 403


async def test_upload_photo_listing_not_found(
    client: AsyncClient, agent_token: str
):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp = await client.post(
            "/api/files/upload?listing_id=00000000-0000-0000-0000-000000000000",
            files={"files": ("test.png", BytesIO(_FAKE_PNG), "image/png")},
            headers={"Authorization": f"Bearer {agent_token}"},
        )
    assert resp.status_code == 404


# ── DELETE /api/files/{photo_id} ──────────────────────────────────────────────

async def test_delete_photo_success(
    client: AsyncClient, listing: dict, agent_token: str
):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        upload_resp = await client.post(
            f"/api/files/upload?listing_id={listing['id']}",
            files={"files": ("test.png", BytesIO(_FAKE_PNG), "image/png")},
            headers={"Authorization": f"Bearer {agent_token}"},
        )
        photo_id = upload_resp.json()[0]["id"]

        resp = await client.delete(
            f"/api/files/{photo_id}",
            headers={"Authorization": f"Bearer {agent_token}"},
        )
    assert resp.status_code == 204


async def test_delete_photo_not_found(client: AsyncClient, agent_token: str):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        resp = await client.delete(
            "/api/files/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {agent_token}"},
        )
    assert resp.status_code == 404


async def test_delete_photo_unauthorized(
    client: AsyncClient, listing: dict, agent_token: str
):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        upload_resp = await client.post(
            f"/api/files/upload?listing_id={listing['id']}",
            files={"files": ("test.png", BytesIO(_FAKE_PNG), "image/png")},
            headers={"Authorization": f"Bearer {agent_token}"},
        )
    photo_id = upload_resp.json()[0]["id"]

    resp = await client.delete(f"/api/files/{photo_id}")
    assert resp.status_code == 401


# ── PATCH /api/files/reorder ──────────────────────────────────────────────────

async def test_reorder_photos(
    client: AsyncClient, listing: dict, agent_token: str
):
    with patch("app.files.service._s3_client", return_value=_mock_s3()):
        upload_resp = await client.post(
            f"/api/files/upload?listing_id={listing['id']}",
            files=[
                ("files", ("p1.png", BytesIO(_FAKE_PNG), "image/png")),
                ("files", ("p2.png", BytesIO(_FAKE_PNG), "image/png")),
            ],
            headers={"Authorization": f"Bearer {agent_token}"},
        )
    photos = upload_resp.json()
    reorder_payload = {
        "photos": [
            {"photo_id": photos[0]["id"], "order": 1},
            {"photo_id": photos[1]["id"], "order": 0},
        ]
    }
    resp = await client.patch(
        f"/api/files/reorder?listing_id={listing['id']}",
        json=reorder_payload,
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 200
