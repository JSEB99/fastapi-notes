from sqlalchemy.orm import Session, selectinload, joinedload
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
                joinedload(PostORM.author),
            ).where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tag_names)))
            .order_by(PostORM.id.asc())
        )

        return self.db.execute(post_list).scalars().all()

    def ensure_author(self, name: str, email: str) -> AuthorORM:
        "Revisar que exista el autor sino lo crea"
        author_obj = self.db.execute(
            select(AuthorORM).where(AuthorORM.email == email)
        ).scalar_one_or_none()

        if author_obj:
            return author_obj
        # Sino existe el autor lo crea
        author_obj = AuthorORM(
            name=name,
            email=email
        )
        # Agregr el autor
        self.db.add(author_obj)
        # Asignar el ID antes del commit
        self.db.flush()

        return author_obj  # El commit se hace desde el endpoint

    def ensure_tag(self, name: str) -> TagORM:
        "Revisar que exista el tag sino lo crea"
        tag_obj = self.db.execute(
            select(TagORM).where(TagORM.name.ilike(name))
        ).scalar_one_or_none()

        if tag_obj:
            return tag_obj

        tag_obj = TagORM(name=name)
        # Agrego
        self.db.add(tag_obj)
        # Genero ID
        self.db.flush()

        return tag_obj

    def create_post(self, title: str, content: str, author: Optional[dict], tags: list[dict]) -> PostORM:
        """Crear un post"""
        # Recibe el objeto json del endpoint
        author_obj = None
        if author:
            author = self.ensure_author(
                author.get("name"), author.get("email")
            )
        post = PostORM(title, content, author)

        for tag in tags:
            tag_obj = self.ensure_tag(tag.get("name"))
            post.tags.append(tag_obj)

        self.db.add(post)
        self.db.flush()  # Asegurar el ID
        self.db.refresh(post)

        return post

    def update_post(self, post: PostORM, updates: Optional[dict]) -> PostORM:
        for key, value in updates.items():
            # Reasignación de valor
            setattr(post, key, value)

        self.db.refresh(post)
        return post

    def delete_post(self, post: PostORM) -> None:
        self.db.delete(post)
