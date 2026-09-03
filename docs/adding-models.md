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

from app.extensions import dbase


class Note(dbase.Model):
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

Notes on the style used here (SQLAlchemy 2.0):
- `Mapped[type]` + `mapped_column(...)` is the modern, type-checked way to
  declare columns. Prefer it over the old `Column(db.Integer, ...)` style.
- `db.Model` is the declarative base provided by Flask-SQLAlchemy — always
  inherit from it, never from a plain `DeclarativeBase` you define yourself.
- Use `db` from `app.extensions`, never instantiate your own `SQLAlchemy()`.

## 2. Register it in `app/models/__init__.py`

```python
from app.models.note import Note  # noqa: F401
```

**Why this step matters:** SQLAlchemy only knows about a model once its
class body has actually executed. Two things depend on that:
- **Tests:** `create_app()` calls `db.create_all()` for the in-memory test
  database, which only creates tables for models it's seen.
- **Migrations:** `flask db migrate` (see below) autogenerates a schema diff
  by comparing your models against the database — a model Python never
  imported is invisible to it too.

If you never import `Note` somewhere, Python never runs the class body, and
`notes` silently never shows up anywhere. Importing it in
`models/__init__.py` (which `create_app` already imports) is what makes
both of these work automatically.

## 3. Generate and apply a migration

Tests get their table for free via `db.create_all()` (see
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

## 4. Add a Marshmallow schema for it

If this model will be exposed over an API, add a schema next to it in
`app/models/note.py`. This project uses **`flask-marshmallow` +
`marshmallow-sqlalchemy`**, which lets you auto-generate a schema's fields
directly from the model — you don't redeclare every column by hand:

```python
from app.extensions import dbase, marsh


class NoteSchema(marsh.SQLAlchemyAutoSchema):
  class Meta:
    model = Note
    load_instance = True  # .load() returns a Note instance, not a dict
    sqla_session = dbase.session
    include_fk = True  # include foreign key columns, if any


note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)
```

`load_instance = True` means `note_schema.load(data)` returns an actual
`Note(...)` instance (ready to `db.session.add()`), not a plain dict —
usually what you want when the schema maps 1:1 to a model.

Use it in a route like:

```python
from app.models.note import Note, note_schema, notes_schema

@bp.route("/notes", methods=["GET"])
def list_notes():
    notes = db.session.query(Note).all()
    return notes_schema.dump(notes)

@bp.route("/notes", methods=["POST"])
def create_note():
    note = note_schema.load(request.get_json())  # raises ValidationError on bad input
    db.session.add(note)
    db.session.commit()
    return note_schema.dump(note), 201
```

### When to skip auto-generation and write fields by hand

`SQLAlchemyAutoSchema` is the default choice when a schema maps closely to a
model. Fall back to plain fields (`fields.Str()`, etc., either on a
`ma.Schema` or a plain `marshmallow.Schema`) when the schema's shape
genuinely diverges from the model — e.g., a request schema that only
accepts a subset of fields, an endpoint that combines multiple models into
one response, or a field that needs custom validation/serialization logic
`Meta.model` can't express. You can still override/add individual fields on
top of an auto schema:

```python
class NoteSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Note
        load_instance = True
        sqla_session = db.session

    title = ma.auto_field(validate=validate.Length(min=1, max=120))
```

## Common mistakes to avoid

- **Forgetting the `models/__init__.py` import** — the #1 cause of "why isn't
  my table being created?"
- **Defining a model class inside a test function.** `db.Model`'s metadata is
  a *shared, process-global* registry on the `db` object — it is **not**
  reset between tests or between `create_app()` calls. Defining a model class
  more than once in the same test session will register duplicate tables and
  can leak schema between tests. See `tests/test_db.py` for the pattern:
  define test-only models once, at module scope.
- **Instantiating your own `SQLAlchemy()`.** Always import the shared `db`
  from `app.extensions`.
- **Forgetting `sqla_session = db.session` in `Meta`** — `SQLAlchemyAutoSchema`
  needs it to build `load_instance=True` results and resolve relationships.
- **Init order:** `db.init_app(app)` must run before `ma.init_app(app)` in
  `create_app()` — flask-marshmallow's SQLAlchemy integration depends on it.
  This is already correct in `app/__init__.py`; just don't reorder it.
