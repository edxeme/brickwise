"""Punto de entrada de la API de Brickwise (FastAPI)."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from . import auth, db, models, reports, setbacks
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
app.include_router(auth.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "brickwise"}


@app.get(
    "/projects/{project_id}/report.md",
    response_class=PlainTextResponse,
)
def project_report(
    project_id: int,
    user: auth.models.User = Depends(auth.get_current_user),
    session: db.Session = Depends(db.get_session),
) -> PlainTextResponse:
    """Informe de factibilidad del proyecto en Markdown (descarga)."""
    project = session.get(models.Project, project_id)
    if project is None or (project.team_id is None or project.team_id != user.team_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    report = reports.build_report(project)
    filename = f"informe-factibilidad-{project_id}.md"
    return PlainTextResponse(
        report,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class SetbackPreviewInput(BaseModel):
    coordinates: list[tuple[float, float]] = Field(min_length=3)
    setback_m: float = Field(ge=0)


@app.post("/setbacks/preview")
def setbacks_preview(
    payload: SetbackPreviewInput,
    _: auth.models.User = Depends(auth.get_current_user),
) -> dict:
    """Polígono edificable tras aplicar el retiro normativo (en metros)."""
    result = setbacks.compute_setback(
        [(c[0], c[1]) for c in payload.coordinates], payload.setback_m
    )
    return {
        "valid": result.valid,
        "message": result.message,
        "buildable": [[lat, lon] for lat, lon in result.buildable],
        "lotAreaM2": result.lot_area_m2,
        "buildableAreaM2": result.buildable_area_m2,
    }
