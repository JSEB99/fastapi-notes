from fastapi.security import OAuth2PasswordBearer
from datetime import UTC, date, timedelta, timezone, datetime
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
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


def decode_token(token: str) -> dict:
    "Decodificar token"
    payload = jwt.decode(
        jwt=token, key=Settings.JWT_SECRET,
        algorithms=[Settings.JWT_ALG])

    return payload

# def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
#     "Crear token de accesso"
#     to_encode = data.copy()
#     expire = datetime.now(
#         tz=timezone.utc) + (expires_delta or timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})

#     token = jwt.encode(
#         payload=to_encode,
#         key=Settings.JWT_SECRET, algorithm=Settings.JWT_ALG)

#     return token


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

        return {"email": sub, "username": username}

    except ExpiredSignatureError:
        raise raise_expired_token()  # Enviado como función

    except InvalidTokenError:
        raise credentials_exc  # Enviado como variable


def hash_password(raw_pass: str) -> str:
    return password_hash.hash(raw_pass)


def verify_password(raw_pass: str, hashed_pass: str) -> bool:
    return password_hash.verify(raw_pass, hashed_pass)
