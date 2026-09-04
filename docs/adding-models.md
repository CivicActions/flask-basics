# Adding a Model

Models live in `app/models/`. There's one model per file, and every model
must be imported in `app/models/__init__.py` or SQLAlchemy will never know it
exists (more on why below).

## 1. Create the model file

Say you're adding a `Note` model. Create `app/models/note.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Note {self.id} {self.title!r}>"
```

If your model just needs `id`/`created_at`/`updated_at` and nothing else
special, inherit from `app.models.base.BaseModel` instead of `Base` directly
— see `app/models/page.py` for a real example.

Notes on the style used here (SQLAlchemy 2.0):
- `Mapped[type]` + `mapped_column(...)` is the modern, type-checked way to
  declare columns. Prefer it over the old `Column(db.Integer, ...)` style.
- `Base` (from `app.extensions`) is the declarative base passed as
  `model_class` to Flask-SQLAlchemy — always inherit from it, never from a
  plain `DeclarativeBase` you define yourself. Don't use `dbase.Model`
  instead: it's the same base at runtime, but it's assigned dynamically
  inside `SQLAlchemy.__init__`, so mypy can't resolve it as a base class.
- Use `dbase` from `app.extensions` for querying/sessions (e.g.
  `dbase.session`), never instantiate your own `SQLAlchemy()`.

## 2. Register it in `app/models/__init__.py`

```python
from app.models.note import Note  # noqa: F401
```

**Why this step matters:** SQLAlchemy only knows about a model once its
class body has actually executed. Two things depend on that:
- **Tests:** `create_app()` calls `dbase.create_all()` for the in-memory test
  database, which only creates tables for models it's seen.
- **Migrations:** `flask db migrate` (see below) autogenerates a schema diff
  by comparing your models against the database — a model Python never
  imported is invisible to it too.

If you never import `Note` somewhere, Python never runs the class body, and
`notes` silently never shows up anywhere. Importing it in
`models/__init__.py` (which `create_app` already imports) is what makes
both of these work automatically.

## 3. Generate and apply a migration

Tests get their table for free via `dbase.create_all()` (see
[`database.md`](database.md) for why), but **development and production
databases do not** — you need to create a migration:

```bash
uv run flask db migrate -m "Add note model"
uv run flask db upgrade
```

The first command writes a new file to `migrations/versions/` — open it and
check it actually says what you expect (see the autogenerate caveats in
[`database.md`](database.md)) before running `upgrade`. Commit the generated
file along with your model change.

## Common mistakes to avoid

- **Forgetting the `models/__init__.py` import** — the #1 cause of "why isn't
  my table being created?"
- **Defining a model class inside a test function.** `Base`'s metadata is
  a *shared, process-global* registry — it is **not** reset between tests or
  between `create_app()` calls. Defining a model class more than once in the
  same test session will register duplicate tables and can leak schema
  between tests. See `tests/test_db.py` for the pattern: define test-only
  models once, at module scope.
- **Instantiating your own `SQLAlchemy()`.** Always import the shared
  `dbase`/`Base` from `app.extensions`.
- **Subclassing `dbase.Model` instead of `Base`.** They're equivalent at
  runtime, but `dbase.Model` is a dynamically assigned instance attribute
  that mypy can't type-check as a base class — use `Base` (or `BaseModel`).

This project is server-rendered (Jinja templates, see
[`templates.md`](templates.md)), so there's no request/response
serialization layer here — routes pass model instances straight into
`render_template()`. If you later add a JSON API, that's the point where a
serialization library (e.g. Marshmallow, or just hand-written `to_dict()`
methods) would earn its keep — don't add one speculatively.
