from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from app.auth.router import router as auth_router
from app.listings.router import router as listings_router
from app.search.router import router as search_router
from app.chat.router import router as chat_router
from app.files.router import router as files_router
from app.admin.router import router as admin_router

app = FastAPI(
    title="Domiq API",
    version="1.0.0",
    description="Маркетплейс недвижимости",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(listings_router, prefix="/api/listings", tags=["Listings"])
app.include_router(search_router,   prefix="/api/search",   tags=["Search"])
app.include_router(chat_router,     prefix="/api/chat",     tags=["Chat"])
app.include_router(files_router,    prefix="/api/files",    tags=["Files"])
app.include_router(admin_router,    prefix="/api/admin",    tags=["Admin"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"status": "ok", "project": "Domiq API"}
