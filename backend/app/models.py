"""Modelos de dominio: proyectos, criterios de factibilidad y normativa vectorizada."""

import datetime as dt
import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Typology(str, enum.Enum):
    VIVIENDA = "vivienda"
    COMERCIO = "comercio"
    INDUSTRIA = "industria"
    MIXTO = "mixto"
    INSTITUCIONAL = "institucional"


class Category(str, enum.Enum):
    TECNICA = "tecnica"
    NORMATIVA = "normativa"
    ECONOMICA = "economica"
    MERCADO = "mercado"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    location: Mapped[str] = mapped_column(String(200))
    typology: Mapped[Typology] = mapped_column(Enum(Typology, name="typology"))
    area_m2: Mapped[float] = mapped_column(Numeric(12, 2))
    budget_cop: Mapped[float] = mapped_column(Numeric(16, 2))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    criteria: Mapped[list["Criterion"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    regulation_chunks: Mapped[list["RegulationChunk"]] = relationship(
        back_populates="project"
    )


class Criterion(Base):
    """Criterio de factibilidad con peso (1–5) y calificación (0–100)."""

    __tablename__ = "criteria"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    category: Mapped[Category] = mapped_column(
        Enum(Category, name="criterion_category")
    )
    name: Mapped[str] = mapped_column(String(160))
    weight: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Numeric(5, 2))
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    project: Mapped[Project] = relationship(back_populates="criteria")


class RegulationChunk(Base):
    """Fragmento de documento normativo con su embedding para búsqueda semántica."""

    __tablename__ = "regulation_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    document_title: Mapped[str] = mapped_column(String(200))
    section: Mapped[str | None] = mapped_column(String(200), default=None)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(), nullable=True)

    project: Mapped[Project | None] = relationship(
        back_populates="regulation_chunks"
    )
