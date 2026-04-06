import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── GET /api/search/autocomplete ─────────────────────────────────────────────

async def test_autocomplete_no_results(client: AsyncClient):
    resp = await client.get("/api/search/autocomplete?q=Несуществующий")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


async def test_autocomplete_with_results(client: AsyncClient, listing: dict):
    resp = await client.get("/api/search/autocomplete?q=Мос")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["city"] == "Москва"
    assert items[0]["count"] == 1


async def test_autocomplete_too_short_query(client: AsyncClient):
    resp = await client.get("/api/search/autocomplete?q=М")
    assert resp.status_code == 422


async def test_autocomplete_missing_query(client: AsyncClient):
    resp = await client.get("/api/search/autocomplete")
    assert resp.status_code == 422


# ── GET /api/search — FTS (требует PostgreSQL, пропускается с SQLite) ─────────

@pytest.mark.skip(reason="FTS использует to_tsvector/plainto_tsquery — только PostgreSQL")
async def test_search_fts_by_title(client: AsyncClient, listing: dict):
    resp = await client.get("/api/search?q=Квартира")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.skip(reason="FTS использует to_tsvector/plainto_tsquery — только PostgreSQL")
async def test_search_fts_no_results(client: AsyncClient, listing: dict):
    resp = await client.get("/api/search?q=нетакогослова12345")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.skip(reason="FTS использует to_tsvector/plainto_tsquery — только PostgreSQL")
async def test_search_fts_with_city_filter(client: AsyncClient, listing: dict):
    resp = await client.get("/api/search?q=Квартира&city=Москва")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    resp2 = await client.get("/api/search?q=Квартира&city=Питер")
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0


async def test_search_query_too_short(client: AsyncClient):
    resp = await client.get("/api/search?q=а")
    assert resp.status_code == 422


async def test_search_missing_query(client: AsyncClient):
    resp = await client.get("/api/search")
    assert resp.status_code == 422
