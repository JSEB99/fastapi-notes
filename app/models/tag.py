from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Se recomienda de esta forma ya que evita importaciones circularees
    from .post import PostORM


class TagORM(Base):  # Tabla Etiquetas
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    # Relación inversa con Posts
    posts: Mapped[list["PostORM"]] = relationship(
        secondary="post_tags",  # Lo pase a texto
        back_populates="tags",
        lazy="selectin",
        passive_deletes=True
    )
