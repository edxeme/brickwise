"""Primitivas de seguridad: contraseñas con bcrypt y sesiones con JWT."""

import datetime as dt

import bcrypt
import jwt

from .config import SECRET_KEY, TOKEN_TTL_DAYS

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    now = dt.datetime.now(dt.UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + dt.timedelta(days=TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> int | None:
    """Devuelve el user_id del token válido, o None si expiró o es inválido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    subject = payload.get("sub")
    try:
        return int(subject) if subject is not None else None
    except ValueError:
        return None
