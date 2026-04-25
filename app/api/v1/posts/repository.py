from fastapi import Depends
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select, func
from typing import Optional
from app.core.security import get_current_user
from app.models import PostORM, User, TagORM
from math import ceil

from app.models.user import User
from app.utils.slugify_utils import ensure_unique_slug


class PostRepository:
    def __init__(self, db: Session):
        """Crear sesion por objeto"""
        self.db = db

    def get(self, post_id: int) -> Optional[PostORM]:
        """Traer todo lo relacionado con un post"""
        return self.db.get(PostORM, post_id)

    def get_by_slug(self, slug: str) -> Optional[PostORM]:
        """Obtener datos por slug"""
        query = (select(PostORM).where(PostORM.slug == slug))
        return self.db.execute(query).scalar_one_or_none()

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

    def by_tags(self, tags: list[str]) -> list[PostORM]:
        """Listado de posts por uno o mas tags"""
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
                # Evitar problema n+1 al serializar
                selectinload(PostORM.tags),
                joinedload(PostORM.user),
            ).where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tag_names)))
            .order_by(PostORM.id.asc())
        )

        return self.db.execute(post_list).scalars().all()

    def ensure_user(self, name: str, email: str) -> User:
        "Revisar que exista el autor sino lo crea"
        user_obj = self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        # Retornarlo y listo
        return user_obj  # El commit se hace desde el endpoint

    def ensure_tag(self, name: str) -> TagORM:
        "Revisar que exista el tag sino lo crea"

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

    def create_post(
            self,
            title: str,
            content: str,
            tags: list[dict],
            image_url: Optional[str],
            category_id: Optional[int],
            user: User = Depends(get_current_user)
    ) -> PostORM:
        """Crear un post"""
        # Recibe el objeto json del endpoint
        user_obj = None
        if user:
            user_obj = self.ensure_user(
                # name => username debido al get_current_user
                user.full_name, user.email
            )

        # Generamos slug automatico
        unique_slug = ensure_unique_slug(self.db, title)

        post = PostORM(
            title=title,
            slug=unique_slug,
            content=content,
            user=user_obj,
            image_url=image_url,
            category_id=category_id
        )

        names = tags[0]["name"].split(",")
        for name in names:
            name = name.strip().lower()
            if not name:
                continue
            tag_obj = self.ensure_tag(name)
            post.tags.append(tag_obj)

        self.db.add(post)
        self.db.flush()  # Asegurar el ID
        self.db.refresh(post)

        return post

    def update_post(self, post: PostORM, updates: Optional[dict]) -> PostORM:
        for key, value in updates.items():
            # Reasignación de valor
            setattr(post, key, value)

        return post

    def delete_post(self, post: PostORM) -> None:
        self.db.delete(post)
