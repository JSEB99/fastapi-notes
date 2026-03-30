from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Se recomienda de esta forma ya que evita importaciones circularees
    from .post import PostORM


class AuthorORM(Base):  # Tabla Autores
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False)

    # Relación con Posts
    posts: Mapped[list["PostORM"]] = relationship(back_populates="author")
    # 1 Author tenga muchos posts
