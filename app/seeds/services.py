from contextlib import contextmanager
from typing import Optional

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.category import CategoryORM
from app.models.tag import TagORM
from app.models.user import User
from app.seeds.data.categories import CATEGORIES
from app.seeds.data.tags import TAGS
from app.seeds.data.users import USERS


def hash_password(raw: str) -> str:
    return PasswordHash.recommended().hash(raw)


# Asegurar que algo se ejecute al principio y al final (aunque existen errores entre medias)
@contextmanager
def atomic(db: Session):
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise

# Idempotencia


def _user_by_email(db: Session, email: str) -> Optional[User]:
    return db.execute(select(User).where(User.email == email)).scalars().first()


def _category_by_slug(db: Session, slug: str) -> Optional[CategoryORM]:
    return db.execute(select(CategoryORM).where(CategoryORM.slug == slug)).scalars().first()


def _tag_by_name(db: Session, name: str) -> Optional[TagORM]:
    return db.execute(select(TagORM).where(TagORM.name == name)).scalars().first()

# Primer Seed


def seed_users(db: Session) -> None:
    with atomic(db):
        for data in USERS:
            obj = _user_by_email(db, data["email"])
            if obj:
                # UPDATE
                changed = False
                if obj.full_name != data.get("full_name"):
                    # Actualización de nombre
                    obj.full_name = data.get("full_name")
                    changed = True
                if data.get("password"):
                    # Actualizar contraseña
                    obj.hashed_pass = hash_password(data.get("password"))
                    changed = True
                if data.get("role"):
                    # Actualizar role
                    obj.role = data.get("role")
                    changed = True
                if changed:
                    db.commit()
                    db.refresh(obj)
            else:
                # INSERTAR
                db.add(User(
                    email=data["email"],
                    full_name=data["full_name"],
                    role=data["role"],
                    hashed_pass=hash_password(data["password"])
                ))


def seed_categories(db: Session) -> None:
    with atomic(db):
        for data in CATEGORIES:
            obj = _category_by_slug(db, data["slug"])
            if obj:
                if obj.name != data.get("name"):
                    obj.name = data.get("name")
            else:
                db.add(CategoryORM(name=data.get("name"), slug=data.get("slug")))


def seed_tags(db: Session) -> None:
    with atomic(db):
        for data in TAGS:
            obj = _tag_by_name(db, data["name"])
            if obj:
                if obj.name != data["name"]:
                    obj.name = data["name"]
            else:
                db.add(TagORM(name=data["name"]))


def run_users() -> None:
    """Carga de usuarios"""
    with SessionLocal() as db:
        seed_users(db)


def run_categories() -> None:
    """Carga categorias"""
    with SessionLocal() as db:
        seed_categories(db)


def run_tags() -> None:
    """Carga de tags"""
    with SessionLocal() as db:
        seed_tags(db)


# Los cargue todos
def run_all() -> None:
    """Carga de las Seeds"""
    with SessionLocal() as db:
        seed_users(db)
        seed_categories(db)
        seed_tags(db)
