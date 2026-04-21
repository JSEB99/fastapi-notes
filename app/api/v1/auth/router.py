from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth.repository import UserRepository
from app.core.db import get_db
from app.models.user import User
from .schemas import TokenResponse, UserCreate, UserLogin, UserPublic
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    repository = UserRepository(db)
    if repository.get_by_email(payload.email):
        raise HTTPException(
            status_code=400,
            detail="Email ya registrado"
        )
    user = repository.create(
        email=payload.email,
        hashed_pass=hash_password(payload.hashed_pass),
        full_name=payload.full_name
    )

    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    repository = UserRepository(db)
    user = repository.get_by_email(payload.email)

    if not user or not verify_password(payload.raw_pass, payload.hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas"
        )

    token = create_access_token(sub=str(user.id))

    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
# No bloquear el servidor mientras llamo esta ruta
# En lo que se resuelve, este en 2do plano
async def read_me(current: User = Depends(get_current_user)):
    # Al momento de depender de get_current_user
    # Mediante esa dependencia le pide el token valida
    return UserPublic.model_validate(current)
