---
name: new-module
description: Scaffold a new FastAPI module with router, models, schemas, service files and register it in main.py
disable-model-invocation: true
argument-hint: <module-name>
---

Create a new FastAPI module called `$ARGUMENTS` for the Domiq backend.

## Steps

1. Create the directory `app/$ARGUMENTS/` with these files:

**`app/$ARGUMENTS/__init__.py`** — empty file

**`app/$ARGUMENTS/models.py`** — SQLAlchemy model following this pattern:
```python
import uuid
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class $ARGUMENTS(Base):  # use CamelCase
    __tablename__ = "$ARGUMENTS"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    # TODO: add fields
```

**`app/$ARGUMENTS/schemas.py`** — Pydantic schemas:
```python
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class $ARGUMENTSCreate(BaseModel):
    pass  # TODO: add fields

class $ARGUMENTSUpdate(BaseModel):
    pass  # TODO: add optional fields

class $ARGUMENTSResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
```

**`app/$ARGUMENTS/service.py`** — business logic:
```python
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import $ARGUMENTS  # CamelCase
from .schemas import $ARGUMENTSCreate, $ARGUMENTSUpdate

async def get_all(db: AsyncSession) -> list:
    result = await db.execute(select($ARGUMENTS))
    return result.scalars().all()

async def get_by_id(db: AsyncSession, id: UUID):
    result = await db.execute(select($ARGUMENTS).where($ARGUMENTS.id == id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="$ARGUMENTS not found")
    return item

async def create(db: AsyncSession, data: $ARGUMENTSCreate):
    item = $ARGUMENTS(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item
```

**`app/$ARGUMENTS/router.py`** — FastAPI router:
```python
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from . import service
from .schemas import $ARGUMENTSCreate, $ARGUMENTSResponse

router = APIRouter()

@router.get("/", response_model=list[$ARGUMENTSResponse])
async def get_all(db: AsyncSession = Depends(get_db)):
    return await service.get_all(db)

@router.get("/{id}", response_model=$ARGUMENTSResponse)
async def get_one(id: UUID, db: AsyncSession = Depends(get_db)):
    return await service.get_by_id(db, id)

@router.post("/", response_model=$ARGUMENTSResponse, status_code=201)
async def create(data: $ARGUMENTSCreate, db: AsyncSession = Depends(get_db)):
    return await service.create(db, data)
```

2. Register the router in `main.py`:
```python
from app.$ARGUMENTS.router import router as ${ARGUMENTS}_router
app.include_router(${ARGUMENTS}_router, prefix="/api/$ARGUMENTS", tags=["$ARGUMENTS"])
```

3. Import the model in `migrations/env.py` so Alembic detects it:
```python
from app.$ARGUMENTS.models import $ARGUMENTS  # CamelCase
```

4. Show me all created files and ask if I want to create an Alembic migration for the new model.
