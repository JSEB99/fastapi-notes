from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.v1.categories.repository import CategoryRepository
from app.core.db import get_db
from app.api.v1.categories.schemas import CategoryCreate, CategoryUpdate, CategoryPublic
from app.models.category import CategoryORM

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryPublic])
def list_categories(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)

    return repository.list_many(skip=skip, limit=limit)


@router.get("", response_model=tuple[int, list[CategoryORM]])
def list_cat_totals(page: int = 0, per_page: int = 50, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)

    return repository.list_with_total(page=page, per_page=per_page)


@router.post("", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)

    exist = repository.get_by_slug(data.slug)
    if exist:
        raise HTTPException(
            status_code=400,
            detail="slug en uso"
        )
    try:
        category = repository.create(name=data.name, slug=data.slug)
        db.commit()
        db.refresh(category)

        return category
    except SQLAlchemyError:
        # Desaga la operación frente a error
        db.rollback()
        # Notificar error
        raise HTTPException(
            status_code=500, detail="Error al crear la categoría")


@router.get("/{category_id}", response_model=CategoryPublic)
def get_category(category_id: int, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)

    category = repository.get(category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Categoría no encontrada"
        )

    return category


@router.put("/{category_id}", response_model=CategoryPublic)
def update_category(category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)

    category = repository.get(category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Categoría no encontrada"
        )

    if not data:
        return CategoryPublic.model_validate(category, from_attributes=True)

    try:
        # Excluya lo que no le envío al dict
        updates = data.model_dump(exclude_unset=True)
        category = repository.update(category, updates)

        db.commit()
        db.refresh(category)

        return CategoryPublic.model_validate(category, from_attributes=True)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al actualizar la categoría {category_id}")


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)
    repository = CategoryRepository(db)

    category = repository.get(category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Categoría no encontrada"
        )

    try:
        repository.delete_post(category)
        db.commit()
        return None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar el post {category_id}")
