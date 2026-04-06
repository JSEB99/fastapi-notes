from fastapi import APIRouter, Query, Depends, Path, HTTPException, status, UploadFile, File
from typing import Annotated, Literal, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from math import ceil
import time
import asyncio
import threading
from app.core.db import get_db
from app.core.security import oauth2_scheme, get_current_user
from app.services.file_storage import save_uploaded_image
from .schemas import (
    PostPublic, PaginatedPost, PostCreate, PostUpdate, PostSummary)
from .repository import PostRepository


# Crear objeto APIRouter
# Definir un prefijo para las URLs (e.g. /posts)
# tags -> metadata documentación
router = APIRouter(prefix="/posts", tags=["posts"])

# Asincronismo ===============================================
# Sincronismo
# @router.get("/sync")
# def sync_endpoint():
#     print("SYNC Thread:", threading.current_thread().name)
#     time.sleep(8)
#     return {"mensaje": "Función sincrona termino"}

# # Asincronismo
# @router.get("/async")
# async def async_endpoint():
#     print("ASYNC Thread:", threading.current_thread().name)
#     await asyncio.sleep(8)
#     # await time.sleep(8)
#     return {"mensaje": "Función sincrona termino"}


# @app -> @router ============================================
# Lista de post public devuelve
@router.get("", response_model=PaginatedPost)  # "" -> "/posts"
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

    repository = PostRepository(db)

    query = query or text

    total, items = repository.search(
        query, order_by, direction, page, per_page)

    total_pages = ceil(total/per_page) if total > 0 else 0
    current_page = 0 if total_pages == 0 else min(page, total_pages-1)
    has_prev = current_page > 0
    has_next = current_page < total_pages - 1

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


@router.get("/by-tags", response_model=list[PostPublic])
def filter_by_tags(
    tags: Annotated[list[str], Query(
        min_length=1,
        description="Una o más etiquetas",
        examples=["?tags=python&tags=fastapi"]
    )],
    db: Session = Depends(get_db)
):

    repository = PostRepository(db)

    return repository.by_tags(tags)


@router.get("/{post_id}", response_model=PostSummary | PostPublic, response_description="Post encontrado")
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
    repository = PostRepository(db)
    post = repository.get(post_id)

    if not post:  # Sino lo encuentra
        raise HTTPException(status_code=404, detail="Post no encontrado")

    if include_content:
        # model_validate => no busques solo diccionarios tambien atributos del obj
        return PostPublic.model_validate(post, from_attributes=True)
    return PostSummary.model_validate(post, from_attributes=True)


@router.post("", response_model=PostPublic, response_description="Post creado (OK)", status_code=status.HTTP_201_CREATED)
def create_post(post: Annotated[PostCreate, Depends(PostCreate.as_form)], image: Optional[UploadFile] = File(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    # user => valida el usuario
    repository = PostRepository(db)
    saved = None
    try:
        if image:
            saved = save_uploaded_image(image)

        image_url = saved["url"] if saved else None

        new_post = repository.create_post(
            post.title,
            post.content,
            user,  # Le paso el usuario que devuelve get_current_user
            [tag.model_dump() for tag in post.tags],
            image_url
        )
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


@router.put("/{post_id}", response_model=PostPublic, response_description="Post actualizado", response_model_exclude_none=True)
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):

    repository = PostRepository(db)
    post = repository.get(post_id)

    if not post:  # Sino lo encuentra
        raise HTTPException(status_code=404, detail="Post no encontrado")

    if not data:
        return PostPublic.model_validate(post, from_attributes=True)

    try:
        # Excluya lo que no le envío al dict
        updates = data.model_dump(exclude_unset=True)
        post = repository.update_post(post, updates)

        db.commit()
        db.refresh(post)

        return PostPublic.model_validate(post, from_attributes=True)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al actualizar el post {post_id}")


# 204 => Salio bien, pero no regresa contenido
@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):

    repository = PostRepository(db)
    post = repository.get(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    try:
        repository.delete_post(post)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar el post {post_id}")


# Security
@router.get("/secure")
def secure_endpoint(token: str = Depends(oauth2_scheme)):
    # Vamos a depender de oauth2_scheme
    return {"message": "Acceso con token", "token_recibido": token}
