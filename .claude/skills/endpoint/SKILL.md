---
name: endpoint
description: Add a new API endpoint to an existing module. Use when asked to add a route, create an endpoint, or implement a new API method.
disable-model-invocation: true
argument-hint: <METHOD /path description>
---

Add a new endpoint: `$ARGUMENTS`

## Steps

1. Parse the request: identify HTTP method, path, and what it should do.

2. Determine which module this belongs to (auth / listings / search / chat / files / admin).

3. Add to `service.py` — the business logic function first:
```python
async def new_action(db: AsyncSession, ...) -> ...:
    # business logic here
    ...
```

4. Add to `router.py` — the route that calls the service:
```python
@router.METHOD("/path", response_model=SomeResponse, status_code=200)
async def endpoint_name(
    ...,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)  # if auth required
):
    return await service.new_action(db, ...)
```

5. Add or update Pydantic schemas in `schemas.py` if new request/response shapes are needed.

6. Show me all changes made.

7. Ask: "Write a test for this endpoint with /write-tests?"

## Rules
- Never put logic in `router.py` — delegate to `service.py`
- Always add `response_model=` to the decorator
- Use `Depends(role_required("admin"))` for admin-only endpoints
- Return proper HTTP status codes: 201 for create, 204 for delete with no body
