from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import engine, Base
from app.routers import table

# Разрешенные origins (Vercel + локальная разработка)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://localhost:3000",
    # Добавим домен Vercel после деплоя
    os.getenv("FRONTEND_URL", ""),
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Superset-1C Bridge API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[url for url in ALLOWED_ORIGINS if url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(table.router)

@app.get("/")
async def root():
    return {"status": "API работает", "service": "Superset-1C Bridge"}
