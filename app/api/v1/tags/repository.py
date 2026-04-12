from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tag import TagORM


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_tag(self, name: str):
        # Extraido de ensure_tag en repo...posts
        normalize = name.strip().lower()

        tag_obj = self.db.execute(
            select(TagORM).where(func.lower(TagORM.name) == normalize)
        ).scalar_one_or_none()

        if tag_obj:
            return tag_obj

        tag_obj = TagORM(name=name)
        # Agrego
        self.db.add(tag_obj)
        # Genero ID
        self.db.flush()

        return tag_obj

    def list_tags(self, search: Optional[str], order_by: str = "id", direction: str = "asc", page: int = 0, per_page: int = 10):
        query = select(TagORM)

        if search:
            query = query.where(func.lower(
                TagORM.name).ilike(f"%{search.lower()}%"))

        pass
