"""API GraphQL (Strawberry) sobre los modelos de SQLAlchemy."""

import strawberry
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from strawberry.fastapi import BaseContext, GraphQLRouter

from . import feasibility, models, regulations
from .db import get_session
from .embeddings import EmbeddingProvider, make_embedder

TypologyEnum = strawberry.enum(models.Typology)
CategoryEnum = strawberry.enum(models.Category)
RatingEnum = strawberry.enum(feasibility.Rating)


@strawberry.type
class CategoryScoreType:
    category: str
    score: float


@strawberry.type
class FeasibilitySummaryType:
    score: float
    rating: RatingEnum
    by_category: list[CategoryScoreType]
    critical_flags: list[str]


@strawberry.type
class CriterionType:
    id: int
    category: CategoryEnum
    name: str
    weight: int
    score: float
    notes: str | None


@strawberry.type
class ProjectType:
    id: int
    name: str
    location: str
    typology: TypologyEnum
    area_m2: float
    budget_cop: float
    criteria: list[CriterionType]

    @strawberry.field
    def feasibility(self) -> FeasibilitySummaryType:
        result = feasibility.weighted_feasibility(
            feasibility.CriterionInput(
                category=c.category.value,
                name=c.name,
                weight=c.weight,
                score=float(c.score),
            )
            for c in self.criteria
        )
        return FeasibilitySummaryType(
            score=result.score,
            rating=result.rating,
            by_category=[
                CategoryScoreType(category=cs.category, score=cs.score)
                for cs in result.by_category
            ],
            critical_flags=result.critical_flags,
        )


@strawberry.input
class CriterionData:
    category: CategoryEnum
    name: str
    weight: int
    score: float
    notes: str | None = None


@strawberry.input
class CreateProjectInput:
    name: str
    location: str
    typology: TypologyEnum
    area_m2: float
    budget_cop: float
    criteria: list[CriterionData] | None = None


@strawberry.type
class RegulationHitType:
    document_title: str
    section: str | None
    content: str
    similarity: float


class Context(BaseContext):
    def __init__(self, session: Session, embedder: EmbeddingProvider):
        super().__init__()
        self.session = session
        self.embedder = embedder


async def get_context(session: Session = Depends(get_session)) -> Context:
    return Context(session=session, embedder=make_embedder())


def _criterion_type(criterion: models.Criterion) -> CriterionType:
    return CriterionType(
        id=criterion.id,
        category=CategoryEnum(criterion.category),
        name=criterion.name,
        weight=criterion.weight,
        score=float(criterion.score),
        notes=criterion.notes,
    )


def _project_type(project: models.Project) -> ProjectType:
    return ProjectType(
        id=project.id,
        name=project.name,
        location=project.location,
        typology=TypologyEnum(project.typology),
        area_m2=float(project.area_m2),
        budget_cop=float(project.budget_cop),
        criteria=[_criterion_type(c) for c in project.criteria],
    )


@strawberry.type
class Query:
    @strawberry.field
    def projects(self, info: strawberry.Info) -> list[ProjectType]:
        rows = info.context.session.scalars(select(models.Project)).all()
        return [_project_type(p) for p in rows]

    @strawberry.field
    def project(self, info: strawberry.Info, id: int) -> ProjectType | None:
        row = info.context.session.get(models.Project, id)
        return _project_type(row) if row else None

    @strawberry.field
    def search_regulations(
        self,
        info: strawberry.Info,
        query: str,
        project_id: int | None = None,
        top_k: int = 5,
    ) -> list[RegulationHitType]:
        hits = regulations.search_regulations(
            info.context.session,
            info.context.embedder,
            query,
            project_id=project_id,
            top_k=top_k,
        )
        return [
            RegulationHitType(
                document_title=chunk.document_title,
                section=chunk.section,
                content=chunk.content,
                similarity=round(similarity, 4),
            )
            for chunk, similarity in hits
        ]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_project(self, info: strawberry.Info, input: CreateProjectInput) -> ProjectType:
        session: Session = info.context.session
        project = models.Project(
            name=input.name,
            location=input.location,
            typology=models.Typology(input.typology.value),
            area_m2=input.area_m2,
            budget_cop=input.budget_cop,
            criteria=[
                models.Criterion(
                    category=models.Category(c.category.value),
                    name=c.name,
                    weight=c.weight,
                    score=c.score,
                    notes=c.notes,
                )
                for c in input.criteria or []
            ],
        )
        session.add(project)
        session.commit()
        return _project_type(project)

    @strawberry.mutation
    def add_criterion(
        self, info: strawberry.Info, project_id: int, input: CriterionData
    ) -> CriterionType | None:
        session: Session = info.context.session
        if session.get(models.Project, project_id) is None:
            return None
        criterion = models.Criterion(
            project_id=project_id,
            category=models.Category(input.category.value),
            name=input.name,
            weight=input.weight,
            score=input.score,
            notes=input.notes,
        )
        session.add(criterion)
        session.commit()
        return _criterion_type(criterion)

    @strawberry.mutation
    def update_criterion(
        self,
        info: strawberry.Info,
        id: int,
        weight: int | None = None,
        score: float | None = None,
        notes: str | None = None,
    ) -> CriterionType | None:
        session: Session = info.context.session
        criterion = session.get(models.Criterion, id)
        if criterion is None:
            return None
        if weight is not None:
            criterion.weight = weight
        if score is not None:
            criterion.score = score
        if notes is not None:
            criterion.notes = notes
        session.commit()
        return _criterion_type(criterion)

    @strawberry.mutation
    def ingest_regulation(
        self,
        info: strawberry.Info,
        document_title: str,
        content: str,
        project_id: int | None = None,
        section: str | None = None,
    ) -> int:
        session: Session = info.context.session
        rows = regulations.ingest_document(
            session,
            info.context.embedder,
            document_title=document_title,
            content=content,
            project_id=project_id,
            section=section,
        )
        return len(rows)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, context_getter=get_context)
