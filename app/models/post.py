from __future__ import annotations
from datetime import datetime, UTC
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Text, DateTime, UniqueConstraint, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

if TYPE_CHECKING:  # Se recomienda de esta forma ya que evita importaciones circulares
    from .author import AuthorORM
    from .tag import TagORM

# Tabla intermedia para muchos a muchos
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey(
        "posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)


class PostORM(Base):  # Al usar alias permite que podamos modificar Base en un futuro
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint(
        "title", name="unique_post_title"),)  # Titulos unicos
    # nombre: tipo: config
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC))

    # Relación con Author
    author_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("authors.id"), nullable=True)  # Llave foranea
    author: Mapped[Optional["AuthorORM"]] = relationship(
        back_populates="posts")

    # Relación con Tags
    tags: Mapped[list["TagORM"]] = relationship(
        secondary=post_tags,  # Cual tabla ocupare, Post -> post_tags
        back_populates="posts",  # Acceder mediante posts
        lazy="selectin",  # Busqueda mediante un selectin
        passive_deletes=True  # Respetar el delete on cascade
    )
