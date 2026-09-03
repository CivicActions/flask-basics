from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base


class BaseModel(Base):
    """Abstract SQLAlchemy base model with common timestamp columns.

    Every concrete model should inherit from `Base`, the same statically
    typed declarative base passed as `model_class` to Flask-SQLAlchemy (see
    app/extensions.py). It's equivalent to `dbase.Model` at runtime but,
    unlike it, can be used as a base class without confusing mypy. This
    keeps SQLAlchemy inspection, schema generation, and migrations working
    as expected.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
