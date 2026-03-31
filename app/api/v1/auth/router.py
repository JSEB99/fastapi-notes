from fastapi import APIRouter, Depends, HTTPException, status
from .schemas import Token, UserPublic
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_current_user
from datetime import timedelta

FAKE_USERS = {
    "ricardo@example.com": {"email": "ricardo@example.com", "username": "ricardo", "password": "secret123"},
    "alumno@example.com":  {"email": "alumno@example.com",  "username": "alumno",  "password": "123456"},
}

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = FAKE_USERS.get(form_data.username)
    # Validamos el usuario =============================================
    # En caso de que el usuario no exista o la contraseña sea incorrecta
    if not user or user.get("password") != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas"
        )

    # Creamos access token
    token = create_access_token(
        data={"sub": user.get("email"), "username": user.get("username")},
        expires_delta=timedelta(minutes=30)
    )

    # Devolvemos el token
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserPublic)
# No bloquear el servidor mientras llamo esta ruta
# En lo que se resuelve, este en 2do plano
async def read_me(current=Depends(get_current_user)):
    # Al momento de depender de get_current_user
    # Mediante esa dependencia le pide el token valida
    return {"email": current.get("email"), "username": current.get("username")}
