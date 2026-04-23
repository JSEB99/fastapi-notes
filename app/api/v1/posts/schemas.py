from fastapi import Form
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict

from app.api.v1.auth.schemas import UserPublic
from app.api.v1.categories.schemas import CategoryPublic

# Clases de Pydantic

# subclase


class Tag(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta"
    )
    # Acepte objetos del ORM
    model_config = ConfigDict(from_attributes=True)


class Author(BaseModel):
    name: str = Field(
        min_length=4,
        max_length=50,
        description="Nombre del author"
    )
    email: EmailStr = Field(examples=["example@gmail.com"])

    # Acepte objetos del ORM
    model_config = ConfigDict(from_attributes=True)


# Estructura del Post

class PostBase(BaseModel):
    title: str
    content: str | None = "Contenido no disponible"
    # Subclase -----------------------------------------------------
    # = [], nos asegura que se cree una lista nueva por cada objetos
    tags: list[Tag] | None = Field(default_factory=list)
    user: UserPublic | None = "Anónimo"
    image_url: str | None = None
    category: CategoryPublic | None = None

    # Acepte objetos del ORM
    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=100,
        description="Titulo del post (mínimo 3 caracteres, máximo 100)",
        examples=[
            "Mi primer post con Fast API",
            "¿Cómo utilizar Fields en FastAPI"
        ]
    )
    content: str | None = Field(
        default="Contenido no disponible",
        min_length=10,
        description="Contenido del post (mínimo 10 caracteres)",
        examples=[
            "Este es un contenido de ejemplo",
            "Fields permite darle mas condiciones a los campos"
        ]
    )
    category_id: int | None = None
    # Agregando subclase
    tags: list[Tag] = Field(default_factory=list)
    # author: Optional[Author] = None # Queremos ocupar el que esta logueado

    # Validacion personalizada
    @field_validator("title")
    @classmethod  # Manejar a nivel de clase y no de obtejo único
    def not_allowed_title(cls, value: str) -> str:
        NOT_ALLOWED_TITLES = ["spam", " no se ", "123"]
        for not_allowed in NOT_ALLOWED_TITLES:
            if not_allowed in value.lower():
                raise ValueError(
                    "El titulo no puede contener la palabra %s", not_allowed
                )
        return value

    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(min_length=3)],
        content: Annotated[str, Form(min_length=10)],
        category_id: Annotated[int, Form(ge=1)],
        tags: Annotated[list[str] | None, Form()] = None
    ):
        """Asegurar formulario cuando envio archivos"""
        tag_objs = [Tag(name=t) for t in (tags or [])]
        return cls(title=title, content=content, category_id=category_id, tags=tag_objs)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=100)
    content: str | None = None
# Response Model


class PostPublic(PostBase):
    id: int  # Añado lo que hace falta el resto lo heredo
    # Entienda que recibe un obj de SQLAlchemy del Post ORM -> JSON
    model_config = ConfigDict(from_attributes=True)


class PostSummary(BaseModel):
    id: int
    title: str
    # Entienda que recibe un obj de SQLAlchemy del Post ORM -> JSON
    # Entienda y valide objetos
    model_config = ConfigDict(from_attributes=True)


# Dando mas detalle en la salida
class PaginatedPost(BaseModel):
    page: int = Field(ge=0, description="Pagina actual")
    per_page: int = Field(ge=0, description="Items por pagina")
    total: int = Field(ge=0, description="Número total de items")
    total_pages: int = Field(ge=0, description="Número total de páginas")
    has_prev: bool = Field(description="Tiene paginas anteriores")
    has_next: bool = Field(description="Tiene paginas posteriores")
    order_by: Literal["id", "title"] = Field(
        default="id", description="Ordenamiento de los items", examples=["id", "title"])
    direction: Literal["asc", "desc"] = Field(
        default="asc", description="Orden ascendente o descendente", examples=["asc", "desc"])
    search: Annotated[str | None, Field(description="Busqueda")] = None
    items: list[PostPublic] = Field(default_factory=list)
