from slugify import slugify
from sqlalchemy import String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Post(BaseModel):
    """A simple, DB-backed static page (title + HTML body), looked up by
    slug. Pairs with app/templates/pages/post.html and the `/post/<slug>`
    route in app/main/routes.py — see docs/adding-models.md and
    docs/templates.md for the full walkthrough.

    `slug` is auto-generated from `title` (via python-slugify) if not
    supplied explicitly — see the `before_insert` listener below.
    """

    __tablename__ = "posts"

    slug: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True, default=""
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    def __repr__(self) -> str:
        return f"<Page {self.id} {self.slug!r}>"


@event.listens_for(Post, "before_insert")
def generate_slug(mapper, connection, target: Post) -> None:
    """Auto-generate `slug` from `title` if one wasn't set explicitly.

    Runs on insert only — an explicitly-passed slug (e.g. in tests) is left
    untouched, and slugs are stable after creation even if `title` is later
    edited.
    """
    if not target.slug:
        target.slug = slugify(target.title)
