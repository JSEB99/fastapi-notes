from fastapi import APIRouter, Query, Depends, Path, HTTPException
from typing import Annotated, Literal
from sqlalchemy.orm import Session
from math import ceil
from app.core.db import get_db
from .schemas import (
    PostPublic, PaginatedPost, PostCreate, PostUpdate, PostSummary)
from .repository import PostRepository


# Crear objeto APIRouter
# Definir un prefijo para las URLs (e.g. /posts)
# tags -> metadata documentación
router = APIRouter(prefix="/posts", tags=["posts"])


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
