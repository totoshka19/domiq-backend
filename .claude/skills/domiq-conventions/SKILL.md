---
name: domiq-conventions
description: Domiq backend coding conventions. Auto-load when writing any Python, FastAPI, SQLAlchemy or Pydantic code in this project.
---

## Domiq backend — coding conventions

### Module structure (always follow app/auth/ as the reference)
- `router.py` — routes only, no business logic
- `models.py` — SQLAlchemy models with UUID PKs
- `schemas.py` — Pydantic: *Create, *Update, *Response suffixes
- `service.py` — all DB queries and business logic
- `dependencies.py` — only in auth module

### Must-follow rules
1. All DB operations are async — use `AsyncSession`, never `Session`
2. UUID for all primary keys — `default=uuid.uuid4`
3. Always return Pydantic `*Response` schema, never raw SQLAlchemy model
4. Business logic only in `service.py`, never in `router.py`
5. All secrets from `settings` (pydantic-settings), never hardcoded
6. Roles checked via `Depends(role_required("agent"))` dependency
7. Errors always via `raise HTTPException(status_code=..., detail="...")`
8. Type hints on every function — no bare `def func(x):`

### Pydantic v2 pattern
```python
class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
```

### SQLAlchemy 2.0 async query pattern
```python
result = await db.execute(select(Model).where(Model.id == id))
item = result.scalar_one_or_none()
```
