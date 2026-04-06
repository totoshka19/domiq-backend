import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── register ──────────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "new@test.com",
        "password": "password123",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "user"
    assert "hashed_password" not in data


async def test_register_duplicate_email(client: AsyncClient, registered_user: dict):
    resp = await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "password123",
        "full_name": "Duplicate",
    })
    assert resp.status_code == 400
    assert "Email" in resp.json()["detail"]


async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "weak@test.com",
        "password": "123",
        "full_name": "Weak",
    })
    assert resp.status_code == 422


async def test_register_invalid_email(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "password123",
        "full_name": "Bad Email",
    })
    assert resp.status_code == 422


# ── login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient, registered_user: dict):
    resp = await client.post("/api/auth/login", json={
        "email": "user@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, registered_user: dict):
    resp = await client.post("/api/auth/login", json={
        "email": "user@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={
        "email": "ghost@test.com",
        "password": "password123",
    })
    assert resp.status_code == 401


# ── refresh ───────────────────────────────────────────────────────────────────

async def test_refresh_success(client: AsyncClient, registered_user: dict):
    login_resp = await client.post("/api/auth/login", json={
        "email": "user@test.com",
        "password": "password123",
    })
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post("/api/auth/refresh", json={"refresh_token": "bad.token.here"})
    assert resp.status_code == 401


# ── GET /me ───────────────────────────────────────────────────────────────────

async def test_get_me_success(client: AsyncClient, user_token: str):
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"


async def test_get_me_unauthorized(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_get_me_invalid_token(client: AsyncClient):
    resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token"})
    assert resp.status_code == 401


# ── PATCH /me ─────────────────────────────────────────────────────────────────

async def test_update_me_success(client: AsyncClient, user_token: str):
    resp = await client.patch(
        "/api/auth/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"


async def test_update_me_unauthorized(client: AsyncClient):
    resp = await client.patch("/api/auth/me", json={"full_name": "X"})
    assert resp.status_code == 401
