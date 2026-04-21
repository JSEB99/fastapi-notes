from typing import Literal

from fastapi.security import OAuth2PasswordBearer
from datetime import UTC, timedelta, datetime
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.core.db import get_db
from app.models.user import User
from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()
# Esa es la ruta que debe usar el cliente para poderse autenticar
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Alternativas para control de errores ==========================
# Con variables =================================================
credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado",
    headers={"WWW-Authenticate": "Bearer"}
)

# Alt opc 2 con funciones =======================================


def raise_expired_token():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expirado",
        headers={"WWW-Authenticate": "Bearer"}
    )


def raise_forbidden():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos suficientes"
    )


def invalid_credentials():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas"
    )


def decode_token(token: str) -> dict:
    "Decodificar token"
    payload = jwt.decode(
        jwt=token, key=Settings.JWT_SECRET,
        algorithms=[Settings.JWT_ALG])

    return payload


def create_access_token(sub: str, minutes: int | None = None) -> str:
    """Crear token"""
    expire = datetime.now(
        UTC) + timedelta(minutes=minutes or Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": sub, "exp": expire}, key=Settings.JWT_SECRET, algorithm=Settings.JWT_ALG)


async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_token(token)
        sub: str | None = payload.get("sub")  # sujeto
        username: str | None = payload.get("username")  # usuario
        if not sub or not username:
            raise credentials_exc

        user_id = int(sub)

    except ExpiredSignatureError:
        raise raise_expired_token()  # Enviado como función

    except InvalidTokenError:
        raise credentials_exc  # Enviado como variable

    except PyJWTError:
        raise invalid_credentials()

    user = db.get(User, user_id)

    if not user or not user.is_active:
        raise invalid_credentials()

    return user


def hash_password(raw_pass: str) -> str:
    return password_hash.hash(raw_pass)


def verify_password(raw_pass: str, hashed_pass: str) -> bool:
    return password_hash.verify(raw_pass, hashed_pass)


def require_role(min_role: Literal["user", "editor", "admin"]):
    order = {"user": 0, "editor": 1, "admin": 2}

    def evaluation(user: User = Depends(get_current_user)) -> User:
        # Compara los roles para ver si tiene los permisos necesarios
        if order[user.role] < order[min_role]:
            raise raise_forbidden()
        return user

    return evaluation


# Variables a usar en los endpoints
require_user = require_role("user")
require_editor = require_role("editor")
require_admin = require_role("admin")
