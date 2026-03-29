import os
from datetime import datetime, UTC
from typing import Annotated, Literal, Optional
from fastapi import FastAPI, Query, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from sqlalchemy import create_engine, Integer, String, Text, DateTime, select, func, UniqueConstraint, ForeignKey, Table, Column
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
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


# Tabla intermedia para muchos a muchos
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey(
        "posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)


class PostORM(Base):  # Al usar alias permite que podamos modificar Base en un futuro
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint(
        "title", name="unique_post_title"),)  # Titulos unicos
    # nombre: tipo: config
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC))

    # Relación con Author
    author_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("authors.id"), nullable=True)  # Llave foranea
    author: Mapped[Optional["AuthorORM"]] = relationship(
        back_populates="posts")

    # Relación con Tags
    tags: Mapped[list["TagORM"]] = relationship(
        secondary=post_tags,  # Cual tabla ocupare, Post -> post_tags
        back_populates="posts",  # Acceder mediante posts
        lazy="selectin",  # Busqueda mediante un selectin
        passive_deletes=True  # Respetar el delete on cascade
    )


class AuthorORM(Base):  # Tabla Autores
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False)

    # Relación con Posts
    posts: Mapped[list["PostORM"]] = relationship(back_populates="author")
    # 1 Author tenga muchos posts


class TagORM(Base):  # Tabla Etiquetas
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    # Relación inversa con Posts
    posts: Mapped[list["PostORM"]] = relationship(
        secondary=post_tags,
        back_populates="tags",
        lazy="selectin",
        passive_deletes=True
    )


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
    author: Author | None = "Anónimo"

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

    # Agregando subclase
    tags: list[Tag] = Field(default_factory=list)
    author: Optional[Author] = None

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
    )] = 0,
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
        min_length=1,
        description="Una o más etiquetas",
        examples=["?tags=python&tags=fastapi"]
    )],
    db: Session = Depends(get_db)
):
    normalized_tag_names = [
        tag.strip().lower() if tag.strip()
        else tag.lower()
        for tag in tags if tag.strip()]

    if not normalized_tag_names:
        return []

    post_list = (
        select(PostORM)
        # Una query para los posts y luego para las etiquetas
        .options(
            selectinload(PostORM.tags),  # Evitar problema n+1 al serializar
            joinedload(PostORM.author),
        ).where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tag_names)))
        .order_by(PostORM.id.asc())
    )

    posts = db.execute(post_list).scalars().all()

    return posts


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
    author_obj = None
    if post.author:
        author_obj = db.execute(
            select(AuthorORM).where(AuthorORM.email == post.author.email)
        ).scalar_one_or_none()
        if not author_obj:
            author_obj = AuthorORM(
                name=post.author.name,
                email=post.author.email
            )
            # Agregr el autor
            db.add(author_obj)
            # Asignar el ID antes del commit
            db.flush()
    new_post = PostORM(
        title=post.title, content=post.content, author=author_obj)

    for tag in post.tags:
        tag_obj = db.execute(
            select(TagORM).where(TagORM.name.ilike(tag.name))
        ).scalar_one_or_none()
        if not tag_obj:
            tag_obj = TagORM(name=tag.name)
            # Agrego
            db.add(tag_obj)
            # Genero ID
            db.flush()
        # Voy agregando 1 a 1 cada tag
        new_post.tags.append(tag_obj)
    try:
        # Marcar la inserción
        db.add(new_post)
        # Confirmar (Commit)
        db.commit()
        # Traer los valores finales (id, created_at)
        db.refresh(new_post)
        return new_post
    except IntegrityError as e:
        db.rollback()  # Desaga la operación frente a error
        raise HTTPException(status_code=409, detail="El título ya existe")
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
