from fastapi.security import OAuth2PasswordBearer
import os
from datetime import timedelta, timezone, datetime
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
# Recomendado / Estandar (otras opciones RS256, etc.)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Esa es la ruta que debe usar el cliente para poderse autenticar
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    "Crear token de accesso"
    to_encode = data.copy()
    expire = datetime.now(
        tz=timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    token = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)

    return token


def decode_token(token: str) -> dict:
    "Decodificar token"
    payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])

    return payload


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decode_token(token)
        sub: str | None = payload.get("sub")  # sujeto
        username: str | None = payload.get("username")  # usuario
        if not sub or not username:
            raise credentials_exc

        return {"email": sub, "username": username}

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except InvalidTokenError:
        raise credentials_exc
