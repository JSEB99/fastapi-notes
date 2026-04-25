from slugify import slugify as _slugify
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.post import PostORM

# Crear Slug


def slugify_base(title: str) -> str:
    slug = _slugify(title, lowercase=True, separator="-")
    return slug or "post"

# Asegurar Slug único


def ensure_unique_slug(db: Session, slug: str) -> str:
    base = slugify_base(slug)
    existing = db.execute(select(PostORM.slug).where(
        PostORM.slug.like(f"{base}"))).scalars().all()

    if base not in existing:
        return base

    # Agregar números para asegurar unicidad
    i = 2
    candidate = f"{base}-{i}"

    # Comprobar si existe
    while candidate in existing:
        i += 1
        candidate = f"{base}-{i}"

    # Si es único lo retorno
    return candidate
