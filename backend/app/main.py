"""Punto de entrada de la API de Brickwise (FastAPI)."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .db import Base, engine
from .graphql_schema import graphql_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    yield


ALLOWED_ORIGINS = [
    origin
    for origin in os.getenv(
        "BRICKWISE_ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")
    if origin
]

app = FastAPI(title="Brickwise API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(graphql_router, prefix="/graphql")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "brickwise"}
