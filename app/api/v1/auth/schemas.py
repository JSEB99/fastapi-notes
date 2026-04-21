from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["user", "editor", "admin"]


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserPublic(UserBase):
    """Info del usuario"""
    # Ahora extendemos de UserBase
    id: int
    role: Role
    is_active: bool


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=30)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic  # Atributo user para devolverle la info del usuario


class RoleUpdate(BaseModel):
    role: Role


class TokenData(BaseModel):
    """Info del token"""
    sub: str
    username: str
