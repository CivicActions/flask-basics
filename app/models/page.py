from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import dbase
from app.models.base import BaseModel


class Page(BaseModel):
    """A simple, DB-backed static page (title + HTML body), looked up by
    slug. Pairs with app/templates/pages/dynamic.html and the `/p/<slug>`
    route in app/main/routes.py — see docs/adding-models.md and
    docs/templates.md for the full walkthrough.
    """

    __tablename__ = "pages"

    slug: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    def __repr__(self) -> str:
        return f"<Page {self.id} {self.slug!r}>"


class PageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Page
        load_instance = True
        sqla_session = dbase.session

    slug = fields.String(validate=validate.Regexp(r"^[a-z0-9-]+$"))
    title = fields.String(validate=validate.Length(min=1, max=120))


page_schema = PageSchema()
pages_schema = PageSchema(many=True)
