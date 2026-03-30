from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
from app.models import PostORM, AuthorORM, TagORM
from math import ceil


class PostRepository:
    def __init__(self, db: Session):
        """Crear sesion por objeto"""
        self.db = db

    def get(self, post_id: int) -> Optional[PostORM]:
        """Traer todo lo relacionado con un post"""
        return self.db.get(PostORM, post_id)

    def search(self, query: Optional[str], order_by: str, direction: str, page: int, per_page: int) -> tuple[int, list[PostORM]]:
        """Listar los posts mediante una consulta"""
        # Seleccionamos los datos de la tabla
        results = select(PostORM)

        if query:
            # Buscamos la consulta con el ORM
            results = results.where(PostORM.title.ilike(f"%{query}%"))

        # db.scalar es traer un número de una consulta
        # cuenta cuantos hay en una tabla, results lo usamos como subquery de select from
        # 0 si no tenemos nada
        total = self.db.scalar(
            select(func.count()).select_from(results.subquery())) or 0

        if total == 0:
            return 0, []

        order_col = PostORM.id if order_by == "id" else func.lower(
            PostORM.title)

        results_sorted = results.order_by(
            order_col.asc() if direction == "asc" else order_col.desc())
        current_page = min(page, ceil(total/per_page)-1)

        start = (current_page) * per_page
        # Limitar por página con un desfase
        # scalars.all extrae todos los objetos del ORM
        items = self.db.execute(
            # Ya no necesitamos el query param offset
            # De esta forma extraemos explicitamente los datos
            # de la página (realmente es un limite con desfase)
            results_sorted.limit(per_page).offset(start)
        ).scalars().all()

        return total, items
