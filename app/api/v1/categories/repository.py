from typing import Sequence
from unittest import skip

from httpx import delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import user
from app.models.category import CategoryORM
from app.services.pagination import paginate_query


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_many(self, *, skip: int = 0, limit: int = 50) -> Sequence[CategoryORM]:
        # * => solo kwargs arguments
        query = (select(CategoryORM).offset(skip).limit(limit))
        return self.db.execute(query).scalars().all()

    def list_with_total(self, *, page: int = 0, per_page: int = 50) -> tuple[int, list[CategoryORM]]:
        query = paginate_query(
            db=self.db, model=CategoryORM, page=page, per_page=per_page)
        return query["total"], query["items"]

    def get(self, category_id: int) -> CategoryORM | None:
        return self.db.get(CategoryORM, category_id)

    def get_by_slug(self, slug: str) -> CategoryORM | None:
        query = select(CategoryORM).where(CategoryORM.slug == slug)
        return self.db.execute(query).scalars().first()  # El primero sino None

    def create(self, *, name: str, slug: str) -> CategoryORM:
        category = CategoryORM(name=name, slug=slug)
        self.db.add(category)
        self.db.flush()  # Obtener llave primaria
        return category

    def update(self, category: CategoryORM, updates: dict) -> CategoryORM:
        # allowed_items = {"name", "slug"}
        for key, value in updates.items():
            setattr(category, key, value)

        return category

    def delete(self, category: CategoryORM) -> None:
        self.db.delete(category)
