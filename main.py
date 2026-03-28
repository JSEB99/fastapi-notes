import os
from datetime import datetime, UTC
from typing import Annotated, Literal
from fastapi import FastAPI, Query, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from sqlalchemy import create_engine, Integer, String, Text, DateTime, select, func
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
from math import ceil

# Servidor de la DB
# Sino existe crea una base de datos sqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
print("Conectado a:", DATABASE_URL)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# Conexión ======================================
# echo True => muestra el SQL ejecutado, future True => sintaxis moderna, engine_kwargs (solo para sqlite)
engine = create_engine(DATABASE_URL, echo=True, future=True, **engine_kwargs)

# Sesion ========================================
# Autoflush: False => no envía cambios hasta hacer el commit, Autocommit: False => hasta no poner commit no se realiza
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session)

# Declarative Base ==============================
# Definir los modelos ORM como clases


class Base(DeclarativeBase):  # Esto hará de Alias
    pass

# Clases de los modelos


class PostORM(Base):  # Al usar alias permite que podamos modificar Base en un futuro
    __tablename__ = "posts"
    # nombre: tipo: config
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC))


# Metodo para crear las tablas en caso de que no existan
# Accedemos a la conexión y creamos las tablas (recomendado en dev)
# En Prod se usan migraciones
Base.metadata.create_all(bind=engine)

# Por cada endpoint me cree la sesión al ingresar, y la cierre al salir


def get_db():
    """conexión a la base de datos y cierre

    Yields:
        db.SessionLocal: sesion local de la instancia

    returns:
        NoneType
    """
    db = SessionLocal()  # Iniciar sesión local
    try:
        yield db  # Use la conexión y cuando termine ira al finally
    finally:
        db.close()


app = FastAPI(title="Mini Blog")


# subclase
class Tag(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta"
    )


class Author(BaseModel):
    first_name: str = Field(
        min_length=4,
        max_length=50,
        description="Nombre del author"
    )
    last_name: str = Field(
        min_length=4,
        max_length=50,
        description="Apellido del author"
    )
    email: EmailStr = Field(examples=["example@gmail.com"])


# Estructura del Post

class PostBase(BaseModel):
    title: str
    content: str | None = "Contenido no disponible"
    # Subclase -----------------------------------------------------
    # = [], nos asegura que se cree una lista nueva por cada objetos
    tags: list[Tag] | None = Field(default_factory=list)
    author: Author | None = "Anónimo"


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

    # Agregando subclase
    tags: list[Tag] = Field(default_factory=list)
    author: Author | None = "Anónimo"

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


@app.get("/")
def home():
    return {'message': 'Bienvenidos a Mini Blog de JSEBM99'}


# Lista de post public devuelve
@app.get("/posts", response_model=PaginatedPost)
def list_posts(
    page: Annotated[int, Query(
        ge=0,
        description="Página",
        examples=[0]
    )],
    text: Annotated[str, Query(
        description="Texto para buscar por título (Obsoleto, usa 'query' en su lugar)",
        deprecated=True
    )] = None,
    query: Annotated[str, Query(
        description="Texto para buscar por título",
        alias="search",  # Cambio en el query param sin alterar todo el código, ahora podremos usar "search" en vez de "query"
        min_length=3,
        max_length=50,
        pattern=r"^[\w\sáéíóúÁÉÍÓÚüÜ-]+$"  # expresiones regulares
    )] = None,
    per_page: Annotated[int, Query(
        ge=0,
        description="Limite de items por página"
    )] = 10,
    order_by: Annotated[Literal["id", "title"], Query(  # Literal solo permitira esos dos valores
        description="Campo de orden",
    )] = "id",
    direction: Annotated[Literal["asc", "desc"], Query(
        description="Dirección del orden"
    )] = "asc",
    db: Session = Depends(get_db)
):
    # Seleccionamos los datos de la tabla
    results = select(PostORM)

    query = query or text

    if query:
        # Buscamos la consulta con el ORM
        results = results.where(PostORM.title.ilike(f"%{query}%"))

    # db.scalar es traer un número de una consulta
    # cuenta cuantos hay en una tabla, results lo usamos como subquery de select from
    # 0 si no tenemos nada
    total = db.scalar(
        select(func.count()).select_from(results.subquery())) or 0

    if order_by == "id":
        order_col = PostORM.id
    else:
        order_col = func.lower(PostORM.title)

    results_sorted = results.order_by(
        order_col.asc() if direction == "asc" else order_col.desc())
    total_pages = ceil(total/per_page) if total > 0 else 0
    current_page = 0 if total_pages == 0 else min(page, total_pages-1)

    if total_pages == 0:
        items: list[PostORM] = []
    else:
        start = (current_page) * per_page
        # Limitar por página con un desfase
        # scalars.all extrae todos los objetos del ORM
        items = db.execute(
            # Ya no necesitamos el query param offset
            # De esta forma extraemos explicitamente los datos
            # de la página (realmente es un limite con desfase)
            results_sorted.limit(per_page).offset(start)
        ).scalars().all()

    has_prev = current_page > 0
    has_next = False if current_page == total_pages-1 else True

    # Dando mas detalle en la salida
    return PaginatedPost(
        page=current_page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        order_by=order_by,
        search=query,
        items=items
    )


@app.get("/posts/by-tags", response_model=list[PostPublic])
def filter_by_tags(
    tags: Annotated[list[str], Query(
        min_length=2,
        description="Una o más etiquetas",
        examples=["?tags=python&tags=fasapi"]
    )]
):
    tags_lower = [tag.lower() for tag in tags]

    return [
        post for post in BLOG_POST
        if any(
            tag["name"].lower() in tags_lower
            for tag in post.get("tags", [])
        )
    ]


@app.get("/posts/{post_id}", response_model=PostSummary | PostPublic, response_description="Post encontrado")
def get_post_condition(
    post_id: Annotated[
        int,
        Path(
            ge=1,
            title="ID del Post",
            description="Identificador entero del Post debe ser mayor o igual a 1",
            examples=[1]
        )],
    include_content: Annotated[bool, Query(
        description="Incluir o no el contenido")] = True,
    # Enlazamos con la db
    db: Session = Depends(get_db)
):
    # Version optimizada para Primary Keys (No se recomienda con joins)
    post = db.get(PostORM, post_id)  # Buscar el id dentro de la DB

    # Alternativa
    # Declaro sentencia
    # post_find = select(PostORM).where(PostORM.id == post_id)
    # Ejecutar query
    # post = db.execute(post_find).scalar_one_or_none()

    if not post:  # Sino lo encuentra
        raise HTTPException(status_code=404, detail="Post no encontrado")

    if include_content:
        # model_validate => no busques solo diccionarios tambien atributos del obj
        return PostPublic.model_validate(post, from_attributes=True)
    return PostSummary.model_validate(post, from_attributes=True)


@app.post("/posts", response_model=PostPublic, response_description="Post creado (OK)", status_code=status.HTTP_201_CREATED)
# ... elipsis -> obligatorio | Le pasamos la sesion
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    new_post = PostORM(title=post.title, content=post.content)
    try:
        # Marcar la inserción
        db.add(new_post)
        # Confirmar (Commit)
        db.commit()
        # Traer los valores finales (id, created_at)
        db.refresh(new_post)
        return new_post
    except SQLAlchemyError:
        # Desaga la operación frente a error
        db.rollback()
        # Notificar error
        raise HTTPException(status_code=500, detail="Error al crear el Post")


# exclude_none, me excluya los valores que no le envío al endpoint
@app.put("/posts/{post_id}", response_model=PostPublic, response_description="Post actualizado", response_model_exclude_none=True)
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):

    post = db.get(PostORM, post_id)

    if not post:  # Sino lo encuentra
        raise HTTPException(status_code=404, detail="Post no encontrado")

    payload = data.model_dump(exclude_unset=True)

    for key, value in payload.items():
        # Reasignación de valor
        setattr(post, key, value)

    db.commit()
    db.refresh(post)

    return PostPublic.model_validate(post, from_attributes=True)


# 204 => Salio bien, pero no regresa contenido
@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    # Alternativa
    # sqlalchemy import delete
    # del_query = delete(PostORM).where(PostORM.id == post_id)
    # db.execute(del_query)

    db.delete(post)
    db.delete(post)
    db.commit()
    return
