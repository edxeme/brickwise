"""API GraphQL (Strawberry) sobre los modelos de SQLAlchemy.

Toda operación exige un JWT válido (header Authorization del POST /graphql);
los proyectos se limitan al equipo del usuario autenticado.
"""

import strawberry
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from strawberry.fastapi import BaseContext, GraphQLRouter

from . import auth, feasibility, models, regulations
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
    alternative_id: int | None


@strawberry.type
class SiteAlternativeType:
    id: int
    project_id: int
    name: str
    notes: str | None
    criteria: list[CriterionType]

    @strawberry.field
    def feasibility(self) -> FeasibilitySummaryType:
        return _feasibility_summary(self.criteria)


@strawberry.type
class ProjectType:
    id: int
    name: str
    location: str
    typology: TypologyEnum
    area_m2: float
    budget_cop: float
    criteria: list[CriterionType]
    alternatives: list[SiteAlternativeType]

    @strawberry.field
    def feasibility(self) -> FeasibilitySummaryType:
        return _feasibility_summary(self.criteria)


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


@strawberry.input
class CreateAlternativeInput:
    project_id: int
    name: str
    notes: str | None = None


@strawberry.type
class RegulationHitType:
    document_title: str
    section: str | None
    content: str
    similarity: float


class Context(BaseContext):
    def __init__(
        self,
        session: Session,
        embedder: EmbeddingProvider,
        current_user: models.User | None,
    ):
        super().__init__()
        self.session = session
        self.embedder = embedder
        self.current_user = current_user


async def get_context(
    request: Request, session: Session = Depends(get_session)
) -> Context:
    user: models.User | None = None
    authorization = request.headers.get("Authorization")
    if authorization and authorization.lower().startswith("bearer "):
        user_id = auth.decode_token(authorization.split(" ", 1)[1].strip())
        if user_id is not None:
            user = session.get(models.User, user_id)
    return Context(session=session, embedder=make_embedder(), current_user=user)


def require_user(context: Context) -> models.User:
    if context.current_user is None:
        raise Exception("No autenticado: envía un token Bearer en Authorization")
    return context.current_user


def _feasibility_summary(
    criteria: list[CriterionType] | list[models.Criterion],
) -> FeasibilitySummaryType:
    result = feasibility.weighted_feasibility(
        feasibility.CriterionInput(
            category=(
                c.category.value
                if isinstance(c.category, models.Category)
                else str(c.category)
            ),
            name=c.name,
            weight=c.weight,
            score=float(c.score),
        )
        for c in criteria
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


def _criterion_type(criterion: models.Criterion) -> CriterionType:
    return CriterionType(
        id=criterion.id,
        category=CategoryEnum(criterion.category),
        name=criterion.name,
        weight=criterion.weight,
        score=float(criterion.score),
        notes=criterion.notes,
        alternative_id=criterion.alternative_id,
    )


def _alternative_type(alternative: models.SiteAlternative) -> SiteAlternativeType:
    return SiteAlternativeType(
        id=alternative.id,
        project_id=alternative.project_id,
        name=alternative.name,
        notes=alternative.notes,
        criteria=[_criterion_type(c) for c in alternative.criteria],
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
        alternatives=[_alternative_type(a) for a in project.alternatives],
    )


def _team_project(context: Context, project_id: int) -> models.Project | None:
    """Proyecto del equipo del usuario, o None si no existe o es ajeno."""
    user = require_user(context)
    project = context.session.get(models.Project, project_id)
    if project is None or project.team_id != user.team_id:
        return None
    return project


@strawberry.type
class Query:
    @strawberry.field
    def projects(self, info: strawberry.Info) -> list[ProjectType]:
        context: Context = info.context
        user = require_user(context)
        rows = context.session.scalars(
            select(models.Project).where(models.Project.team_id == user.team_id)
        ).all()
        return [_project_type(p) for p in rows]

    @strawberry.field
    def project(self, info: strawberry.Info, id: int) -> ProjectType | None:
        project = _team_project(info.context, id)
        return _project_type(project) if project else None

    @strawberry.field
    def alternatives_comparison(
        self, info: strawberry.Info, project_id: int
    ) -> list[SiteAlternativeType]:
        context: Context = info.context
        project = _team_project(context, project_id)
        if project is None:
            return []
        alternatives = sorted(
            project.alternatives,
            key=lambda a: (
                _feasibility_summary(a.criteria).score,
                len(a.criteria),
            ),
            reverse=True,
        )
        return [_alternative_type(a) for a in alternatives]

    @strawberry.field
    def search_regulations(
        self,
        info: strawberry.Info,
        query: str,
        project_id: int | None = None,
        top_k: int = 5,
    ) -> list[RegulationHitType]:
        context: Context = info.context
        require_user(context)
        hits = regulations.search_regulations(
            context.session,
            context.embedder,
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
    def create_project(
        self, info: strawberry.Info, input: CreateProjectInput
    ) -> ProjectType:
        context: Context = info.context
        user = require_user(context)
        project = models.Project(
            name=input.name,
            location=input.location,
            typology=models.Typology(input.typology.value),
            area_m2=input.area_m2,
            budget_cop=input.budget_cop,
            team_id=user.team_id,
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
        context.session.add(project)
        context.session.commit()
        return _project_type(project)

    @strawberry.mutation
    def add_criterion(
        self, info: strawberry.Info, project_id: int, input: CriterionData
    ) -> CriterionType | None:
        context: Context = info.context
        if _team_project(context, project_id) is None:
            return None
        criterion = models.Criterion(
            project_id=project_id,
            category=models.Category(input.category.value),
            name=input.name,
            weight=input.weight,
            score=input.score,
            notes=input.notes,
        )
        context.session.add(criterion)
        context.session.commit()
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
        context: Context = info.context
        criterion = context.session.get(models.Criterion, id)
        if criterion is None or _team_project(context, criterion.project_id) is None:
            return None
        if weight is not None:
            criterion.weight = weight
        if score is not None:
            criterion.score = score
        if notes is not None:
            criterion.notes = notes
        context.session.commit()
        return _criterion_type(criterion)

    @strawberry.mutation
    def create_alternative(
        self, info: strawberry.Info, input: CreateAlternativeInput
    ) -> SiteAlternativeType | None:
        context: Context = info.context
        if _team_project(context, input.project_id) is None:
            return None
        alternative = models.SiteAlternative(
            project_id=input.project_id,
            name=input.name,
            notes=input.notes,
        )
        context.session.add(alternative)
        context.session.commit()
        return _alternative_type(alternative)

    @strawberry.mutation
    def add_alternative_criterion(
        self, info: strawberry.Info, alternative_id: int, input: CriterionData
    ) -> CriterionType | None:
        context: Context = info.context
        alternative = context.session.get(models.SiteAlternative, alternative_id)
        if alternative is None or _team_project(context, alternative.project_id) is None:
            return None
        criterion = models.Criterion(
            project_id=alternative.project_id,
            alternative_id=alternative.id,
            category=models.Category(input.category.value),
            name=input.name,
            weight=input.weight,
            score=input.score,
            notes=input.notes,
        )
        context.session.add(criterion)
        context.session.commit()
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
        context: Context = info.context
        require_user(context)
        rows = regulations.ingest_document(
            context.session,
            context.embedder,
            document_title=document_title,
            content=content,
            project_id=project_id,
            section=section,
        )
        return len(rows)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, context_getter=get_context)
