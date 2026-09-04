from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Post(BaseModel):
    """A simple, DB-backed static page (title + HTML body), looked up by
    slug. Pairs with app/templates/pages/post.html and the `/p/<slug>`
    route in app/main/routes.py — see docs/adding-models.md and
    docs/templates.md for the full walkthrough.
    """

    __tablename__ = "posts"

    slug: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    def __repr__(self) -> str:
        return f"<Page {self.id} {self.slug!r}>"
