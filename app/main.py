from typing import Annotated, Literal, Optional
from fastapi import FastAPI, Query, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dotenv import load_dotenv

# Servidor de la DB
# Sino existe crea una base de datos sqlite
# PostgreSQL variables
load_dotenv()


# Clases de los modelos


# Metodo para crear las tablas en caso de que no existan
# Accedemos a la conexión y creamos las tablas (recomendado en dev)
# En Prod se usan migraciones
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Mini Blog")


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
    # post = db.get(PostORM, post_id)  # Buscar el id dentro de la DB

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
    # author_obj = None
    # if post.author:
    #     author_obj = db.execute(
    #         select(AuthorORM).where(AuthorORM.email == post.author.email)
    #     ).scalar_one_or_none()
    #     if not author_obj:
    #         author_obj = AuthorORM(
    #             name=post.author.name,
    #             email=post.author.email
    #         )
    #         # Agregr el autor
    #         db.add(author_obj)
    #         # Asignar el ID antes del commit
    #         db.flush()
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
