"""Endpoints REST de autenticación: registro y login."""

from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_session
from . import models
from .security import create_token, decode_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=160)
    team_name: str = Field(min_length=1, max_length=160)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class AuthOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    email: str
    name: str
    team_id: int
    team_name: str


@router.post("/register", response_model=AuthOutput, status_code=201)
def register(payload: RegisterInput, session: Session = Depends(get_session)) -> AuthOutput:
    existing = session.scalar(
        select(models.User).where(models.User.email == payload.email)
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="El correo ya está registrado")

    team = session.scalar(
        select(models.Team).where(models.Team.name == payload.team_name)
    )
    if team is None:
        team = models.Team(name=payload.team_name)
        session.add(team)
        session.flush()

    user = models.User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        team_id=team.id,
    )
    session.add(user)
    session.commit()
    return _auth_output(user)


@router.post("/login", response_model=AuthOutput)
def login(payload: LoginInput, session: Session = Depends(get_session)) -> AuthOutput:
    user = session.scalar(
        select(models.User).where(models.User.email == payload.email)
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return _auth_output(user)


def _auth_output(user: models.User) -> AuthOutput:
    return AuthOutput(
        access_token=create_token(user.id),
        user=UserInfo(
            id=user.id,
            email=user.email,
            name=user.name,
            team_id=user.team_id,
            team_name=user.team.name,
        ),
    )


AuthOutput.model_rebuild()


def get_current_user(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> models.User:
    """Dependencia FastAPI: resuelve el usuario del header Authorization Bearer."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")
    user_id = decode_token(authorization.split(" ", 1)[1].strip())
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = session.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user
