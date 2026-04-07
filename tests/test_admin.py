import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── GET /api/admin/users ──────────────────────────────────────────────────────

async def test_get_users_success(client: AsyncClient, admin_token: str, registered_user: dict):
    resp = await client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


async def test_get_users_forbidden_for_user(client: AsyncClient, user_token: str):
    resp = await client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


async def test_get_users_unauthorized(client: AsyncClient):
    resp = await client.get("/api/admin/users")
    assert resp.status_code == 401


async def test_get_users_search(client: AsyncClient, admin_token: str, registered_user: dict):
    resp = await client.get(
        "/api/admin/users?search=user@test.com",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


# ── PATCH /api/admin/users/{id}/block ─────────────────────────────────────────

async def test_block_user(client: AsyncClient, admin_token: str, registered_user: dict):
    user_id = registered_user["id"]
    resp = await client.patch(
        f"/api/admin/users/{user_id}/block",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_unblock_user(client: AsyncClient, admin_token: str, registered_user: dict):
    user_id = registered_user["id"]
    await client.patch(
        f"/api/admin/users/{user_id}/block",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = await client.patch(
        f"/api/admin/users/{user_id}/unblock",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


async def test_block_nonexistent_user(client: AsyncClient, admin_token: str):
    resp = await client.patch(
        "/api/admin/users/00000000-0000-0000-0000-000000000000/block",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


# ── GET /api/admin/listings ───────────────────────────────────────────────────

async def test_get_admin_listings(client: AsyncClient, admin_token: str, listing: dict):
    resp = await client.get(
        "/api/admin/listings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


async def test_get_admin_listings_forbidden(client: AsyncClient, user_token: str):
    resp = await client.get(
        "/api/admin/listings",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


# ── PATCH /api/admin/listings/{id}/approve ────────────────────────────────────

async def test_approve_listing(client: AsyncClient, admin_token: str, listing: dict):
    resp = await client.patch(
        f"/api/admin/listings/{listing['id']}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_moderated"] is True
    assert data["status"] == "active"


async def test_reject_listing(client: AsyncClient, admin_token: str, listing: dict):
    resp = await client.patch(
        f"/api/admin/listings/{listing['id']}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_moderated"] is False
    assert data["status"] == "archived"


async def test_approve_nonexistent_listing(client: AsyncClient, admin_token: str):
    resp = await client.patch(
        "/api/admin/listings/00000000-0000-0000-0000-000000000000/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


# ── GET /api/admin/stats ──────────────────────────────────────────────────────

async def test_get_stats(client: AsyncClient, admin_token: str, listing: dict):
    resp = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "users_total" in data
    assert "listings_total" in data
    assert data["listings_total"] >= 1


async def test_get_stats_forbidden(client: AsyncClient, user_token: str):
    resp = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403
