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


async def test_get_listing_is_favorite_false_without_auth(client: AsyncClient, listing: dict):
    resp = await client.get(f"/api/listings/{listing['id']}")
    assert resp.status_code == 200
    assert resp.json()["is_favorite"] is False


async def test_get_listing_is_favorite_true_after_add(
    client: AsyncClient, listing: dict, user_token: str
):
    await client.post(
        f"/api/listings/{listing['id']}/favorite",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    resp = await client.get(
        f"/api/listings/{listing['id']}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_favorite"] is True


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
    assert data["total"] == 1
    assert data["items"][0]["id"] == listing["id"]


async def test_get_my_listings_unauthorized(client: AsyncClient):
    resp = await client.get("/api/listings/my")
    assert resp.status_code == 401


async def test_get_my_listings_filter_by_status(
    client: AsyncClient, listing: dict, agent_token: str
):
    # Архивируем объявление
    await client.delete(
        f"/api/listings/{listing['id']}",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    # Создаём новое активное
    await client.post(
        "/api/listings",
        json={**_LISTING_PAYLOAD, "title": "Активное"},
        headers={"Authorization": f"Bearer {agent_token}"},
    )

    active = await client.get(
        "/api/listings/my?status=active",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    archived = await client.get(
        "/api/listings/my?status=archived",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert active.status_code == 200
    assert all(l["status"] == "active" for l in active.json()["items"])
    assert archived.status_code == 200
    assert all(l["status"] == "archived" for l in archived.json()["items"])


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
    data = fav_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == listing["id"]


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


# ── GET /api/listings/{id}/similar ───────────────────────────────────────────

async def test_get_similar_empty(client: AsyncClient, listing: dict):
    """Нет похожих — возвращаем пустой список."""
    resp = await client.get(f"/api/listings/{listing['id']}/similar")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_similar_returns_matches(
    client: AsyncClient, listing: dict, agent_token: str
):
    """Похожее объявление должно попасть в результат."""
    await client.post(
        "/api/listings",
        json={**_LISTING_PAYLOAD, "title": "Другая квартира", "price": "3200000"},
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    resp = await client.get(f"/api/listings/{listing['id']}/similar")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Другая квартира"


async def test_get_similar_excludes_self(client: AsyncClient, listing: dict):
    """Само объявление не должно появляться среди похожих."""
    resp = await client.get(f"/api/listings/{listing['id']}/similar")
    ids = [item["id"] for item in resp.json()]
    assert listing["id"] not in ids


async def test_get_similar_excludes_different_city(
    client: AsyncClient, listing: dict, agent_token: str
):
    """Объявление из другого города не попадает в похожие."""
    await client.post(
        "/api/listings",
        json={**_LISTING_PAYLOAD, "city": "Санкт-Петербург"},
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    resp = await client.get(f"/api/listings/{listing['id']}/similar")
    assert resp.status_code == 200
    assert all(item["city"] == listing["city"] for item in resp.json())


async def test_get_similar_not_found(client: AsyncClient):
    resp = await client.get("/api/listings/00000000-0000-0000-0000-000000000000/similar")
    assert resp.status_code == 404
