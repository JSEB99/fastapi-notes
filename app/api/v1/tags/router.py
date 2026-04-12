from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic
from app.core.db import get_db
from app.core.security import get_current_user


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=dict)
def list_tags(
    page: int = Query(0, ge=0),
    per_page: int = Query(10, ge=1),
    order_by: str = Query("id", pattern="^(id|name)$"),
    direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
    search: Annotated[str | None, Query()] = None,
    db: Session = Depends(get_db)
):
    repository = TagRepository(db)
    return repository.list_tags(search, order_by, direction, page, per_page)


# ruta vacia, cuando envie tags con un posts, cree el post
@router.post("", response_model=TagPublic, response_description="Post creado (ok)", status_code=status.HTTP_201_CREATED)
def create_tag(tag: TagCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = TagRepository(db)
    try:
        tag_created = repository.create_tag(name=tag.name)
        db.commit()
        db.refresh(tag_created)
        return tag_created
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el  tag")
