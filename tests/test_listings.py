import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

_LISTING_PAYLOAD = {
    "title": "Квартира в центре",
    "description": "Уютная квартира",
    "deal_type": "sale",
    "property_type": "apartment",
    "price": "3000000",
    "area": "55.5",
    "rooms": 2,
    "floor": 4,
    "floors_total": 10,
    "address": "ул. Ленина, 10",
    "city": "Москва",
}


# ── POST /api/listings ────────────────────────────────────────────────────────

async def test_create_listing_success(client: AsyncClient, agent_token: str):
    resp = await client.post(
        "/api/listings",
        json=_LISTING_PAYLOAD,
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Квартира в центре"
    assert data["status"] == "active"
    assert data["photos"] == []


async def test_create_listing_unauthorized(client: AsyncClient):
    resp = await client.post("/api/listings", json=_LISTING_PAYLOAD)
    assert resp.status_code == 401


async def test_create_listing_forbidden_user_role(client: AsyncClient, user_token: str):
    resp = await client.post(
        "/api/listings",
        json=_LISTING_PAYLOAD,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_create_listing_invalid_data(client: AsyncClient, agent_token: str):
    resp = await client.post(
        "/api/listings",
        json={"title": "Без обязательных полей"},
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 422


# ── GET /api/listings ─────────────────────────────────────────────────────────

async def test_get_listings_empty(client: AsyncClient):
    resp = await client.get("/api/listings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_get_listings_with_item(client: AsyncClient, listing: dict):
    resp = await client.get("/api/listings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == listing["id"]


async def test_get_listings_filter_by_city(client: AsyncClient, listing: dict):
    resp = await client.get("/api/listings?city=Москва")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp2 = await client.get("/api/listings?city=Питер")
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0


async def test_get_listings_filter_by_deal_type(client: AsyncClient, listing: dict):
    resp = await client.get("/api/listings?deal_type=sale")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp2 = await client.get("/api/listings?deal_type=rent")
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0


async def test_get_listings_pagination(client: AsyncClient, agent_token: str):
    for i in range(3):
        await client.post(
            "/api/listings",
            json={**_LISTING_PAYLOAD, "title": f"Квартира {i}"},
            headers={"Authorization": f"Bearer {agent_token}"},
        )

    resp = await client.get("/api/listings?page=1&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2


# ── GET /api/listings/{id} ────────────────────────────────────────────────────

async def test_get_listing_by_id(client: AsyncClient, listing: dict):
    resp = await client.get(f"/api/listings/{listing['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == listing["id"]


async def test_get_listing_not_found(client: AsyncClient):
    resp = await client.get("/api/listings/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ── PATCH /api/listings/{id} ──────────────────────────────────────────────────

async def test_update_listing_success(client: AsyncClient, listing: dict, agent_token: str):
    resp = await client.patch(
        f"/api/listings/{listing['id']}",
        json={"title": "Обновлённое название"},
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Обновлённое название"


async def test_update_listing_unauthorized(client: AsyncClient, listing: dict):
    resp = await client.patch(
        f"/api/listings/{listing['id']}",
        json={"title": "X"},
    )
    assert resp.status_code == 401


async def test_update_listing_forbidden_other_user(
    client: AsyncClient, listing: dict, user_token: str
):
    resp = await client.patch(
        f"/api/listings/{listing['id']}",
        json={"title": "X"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


# ── DELETE /api/listings/{id} (archive) ───────────────────────────────────────

async def test_archive_listing_success(client: AsyncClient, listing: dict, agent_token: str):
    resp = await client.delete(
        f"/api/listings/{listing['id']}",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "archived"


async def test_archive_listing_unauthorized(client: AsyncClient, listing: dict):
    resp = await client.delete(f"/api/listings/{listing['id']}")
    assert resp.status_code == 401


# ── GET /api/listings/my ──────────────────────────────────────────────────────

async def test_get_my_listings(client: AsyncClient, listing: dict, agent_token: str):
    resp = await client.get(
        "/api/listings/my",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == listing["id"]


async def test_get_my_listings_unauthorized(client: AsyncClient):
    resp = await client.get("/api/listings/my")
    assert resp.status_code == 401


# ── Favorites ─────────────────────────────────────────────────────────────────

async def test_add_and_get_favorite(client: AsyncClient, listing: dict, user_token: str):
    add_resp = await client.post(
        f"/api/listings/{listing['id']}/favorite",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert add_resp.status_code == 204

    fav_resp = await client.get(
        "/api/listings/favorites",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert fav_resp.status_code == 200
    favs = fav_resp.json()
    assert len(favs) == 1
    assert favs[0]["id"] == listing["id"]


async def test_add_favorite_duplicate(client: AsyncClient, listing: dict, user_token: str):
    await client.post(
        f"/api/listings/{listing['id']}/favorite",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    resp = await client.post(
        f"/api/listings/{listing['id']}/favorite",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 400


async def test_remove_favorite(client: AsyncClient, listing: dict, user_token: str):
    await client.post(
        f"/api/listings/{listing['id']}/favorite",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    resp = await client.delete(
        f"/api/listings/{listing['id']}/favorite",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 204


async def test_remove_favorite_not_found(client: AsyncClient, listing: dict, user_token: str):
    resp = await client.delete(
        f"/api/listings/{listing['id']}/favorite",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 404
