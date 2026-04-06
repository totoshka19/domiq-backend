---
name: write-tests
description: Write comprehensive pytest tests for a FastAPI module or endpoint file. Use when asked to test a router, service, or specific endpoint.
disable-model-invocation: true
argument-hint: <path to router.py or module name>
---

Write comprehensive pytest tests for `$ARGUMENTS`.

## Steps

1. Read the target file: `$ARGUMENTS`
2. Identify all endpoints/functions and their expected behavior
3. Write tests in `tests/test_<module_name>.py`

## Test structure — for every protected endpoint write 4 tests:

```python
import pytest
from httpx import AsyncClient

# --- GET endpoints ---
async def test_get_X_success(client: AsyncClient): ...                    # 200
async def test_get_X_not_found(client: AsyncClient): ...                  # 404

# --- POST endpoints ---
async def test_create_X_success(client, agent_token): ...                 # 201
async def test_create_X_unauthorized(client): ...                         # 401 (no token)
async def test_create_X_forbidden(client, user_token): ...                # 403 (wrong role)
async def test_create_X_invalid_data(client, agent_token): ...            # 422

# --- PATCH endpoints ---
async def test_update_X_success(client, agent_token, existing_item): ...  # 200
async def test_update_X_not_owner(client, other_agent_token): ...         # 403

# --- DELETE endpoints ---
async def test_delete_X_success(client, agent_token, existing_item): ... # 200/204
async def test_delete_X_unauthorized(client): ...                         # 401
```

## Use fixtures from conftest.py:
- `client` — AsyncClient connected to test DB
- `user_token` — Bearer token, role: user
- `agent_token` — Bearer token, role: agent
- `admin_token` — Bearer token, role: admin

## Authorization header pattern:
```python
headers = {"Authorization": f"Bearer {agent_token}"}
response = await client.post("/api/listings/", json=data, headers=headers)
```

## After writing tests:
4. Run the tests:
```bash
pytest tests/test_<module_name>.py -v
```
5. If any tests fail — fix them (but do NOT change the production code to make tests pass — fix the tests or report a real bug)
6. Show me the final test results summary
