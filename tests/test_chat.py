import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── POST /api/chat/conversations ──────────────────────────────────────────────

async def test_start_conversation_success(
    client: AsyncClient, listing: dict, user_token: str
):
    resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["listing_id"] == listing["id"]


async def test_start_conversation_idempotent(
    client: AsyncClient, listing: dict, user_token: str
):
    """Повторный запрос возвращает тот же чат, а не создаёт новый."""
    resp1 = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    resp2 = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] == resp2.json()["id"]


async def test_start_conversation_with_self(
    client: AsyncClient, listing: dict, agent_token: str
):
    """Агент не может начать чат по своему объявлению."""
    resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 400


async def test_start_conversation_listing_not_found(
    client: AsyncClient, user_token: str
):
    resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": "00000000-0000-0000-0000-000000000000"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 404


async def test_start_conversation_unauthorized(client: AsyncClient, listing: dict):
    resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
    )
    assert resp.status_code == 401


# ── GET /api/chat/conversations ───────────────────────────────────────────────

async def test_get_my_conversations(
    client: AsyncClient, listing: dict, user_token: str
):
    await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    resp = await client.get(
        "/api/chat/conversations",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["listing_id"] == listing["id"]


async def test_get_my_conversations_empty(client: AsyncClient, user_token: str):
    resp = await client.get(
        "/api/chat/conversations",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_my_conversations_has_other_user_and_unread(
    client: AsyncClient, listing: dict, user_token: str
):
    await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    resp = await client.get(
        "/api/chat/conversations",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()[0]
    assert "other_user" in data
    assert data["other_user"] is not None
    assert "full_name" in data["other_user"]
    assert "unread_count" in data
    assert data["unread_count"] == 0


async def test_get_my_conversations_unauthorized(client: AsyncClient):
    resp = await client.get("/api/chat/conversations")
    assert resp.status_code == 401


# ── GET /api/chat/conversations/{id}/messages ─────────────────────────────────

async def test_get_messages_empty(
    client: AsyncClient, listing: dict, user_token: str
):
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    resp = await client.get(
        f"/api/chat/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_messages_forbidden_for_outsider(
    client: AsyncClient, listing: dict, user_token: str, admin_token: str
):
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    # admin не участник этого чата
    resp = await client.get(
        f"/api/chat/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 403


async def test_get_messages_unauthorized(
    client: AsyncClient, listing: dict, user_token: str
):
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    resp = await client.get(f"/api/chat/conversations/{conv_id}/messages")
    assert resp.status_code == 401


# ── POST /api/chat/conversations/{id}/read ────────────────────────────────────

async def test_mark_read_success(
    client: AsyncClient, listing: dict, user_token: str
):
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    resp = await client.post(
        f"/api/chat/conversations/{conv_id}/read",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 204


async def test_mark_read_unauthorized(
    client: AsyncClient, listing: dict, user_token: str
):
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"listing_id": listing["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    resp = await client.post(f"/api/chat/conversations/{conv_id}/read")
    assert resp.status_code == 401
