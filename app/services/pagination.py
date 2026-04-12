from math import ceil
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 100


def sanitized_pagination(page: int = 0, per_page: int = DEFAULT_PER_PAGE):
    """Traer paginas"""
    page = max(0, int(page or 0))  # Minima sea 0
    per_page = min(MAX_PER_PAGE, max(
        1, int(per_page or 10)))  # Maxima 100 min 1

    return page, per_page


def paginate_query(
    db: Session,
    model,  # No se que modelo este usando
    base_query=None,  # Base de la query
    page: int = 0,
    per_page: int = DEFAULT_PER_PAGE,
    order_by: Optional[str] = None,
    direction: str = "asc",
    allowed_order: Optional[dict[str, Any]] = None
):
    """
    Paginar modelos
    """
    page, per_page = sanitized_pagination(page, per_page)
    query = base_query if base_query is not None else select(
        model)  # Select de tags, posts, etc

    total = db.scalar(
        select(func.count()).select_from(model)) or 0

    if total == 0:
        return {"total": 0, "pages": 0, "page": page, "per_page": per_page, "items": []}

    if allowed_order and order_by:
        col = allowed_order.get(order_by, allowed_order.get("id"))
        query = query.order_by(
            col.desc() if direction == "desc" else col.asc())

    items = db.execute(query.offset(
        (page) * per_page).limit(per_page)).scalars().all()

    return {
        "total": total,
        "pages": ceil(total/per_page),
        "page": page,
        "per_page": per_page,
        "items": items
    }
