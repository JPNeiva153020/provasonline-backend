from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import connect, disconnect
from src.routers.auth import router as auth_router
from src.routers.usuarios import router as usuarios_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await connect()
    yield
    await disconnect()


app = FastAPI(
    title="Seed Backend — Residência de Software II",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(usuarios_router)


@app.get("/", tags=["Health"])
async def root() -> dict:
    return {"status": "ok"}
