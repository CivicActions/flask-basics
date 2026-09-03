# Adding a Route

Routes are grouped into **blueprints** — small, self-contained packages of
related routes. Don't add `@app.route(...)` directly anywhere; always go
through a blueprint. This keeps route logic organized by feature instead of
piling everything into one file, and it's what lets `create_app()` register
routes without needing to know about every individual endpoint.

## Adding a route to an existing blueprint

The `main` blueprint (`app/main/`) is the example already in this repo.
To add a route to it, edit `app/main/routes.py`:

```python
from app.main import bp


@bp.route("/")
def hello_world():
    return "Hello World!"


@bp.route("/ping")
def ping():
    return {"status": "ok"}
```

That's it — no registration step needed, since the whole blueprint is
already registered once in `create_app()`.

## Creating a new blueprint (for a new feature area)

Once a feature has more than a couple of routes, give it its own blueprint
instead of piling everything into `main`. Example: adding a `notes`
blueprint.

**1. Create the package:**

```
app/notes/
├── __init__.py
└── routes.py
```

**2. `app/notes/__init__.py`:**

```python
from flask import Blueprint

bp = Blueprint("notes", __name__, url_prefix="/notes")

from app.notes import routes  # noqa: E402,F401
```

The `url_prefix` means every route in this blueprint is automatically
namespaced — a route defined as `@bp.route("/")` here will actually be
served at `/notes/`.

**3. `app/notes/routes.py`:**

```python
from flask import request

from app.extensions import dbase
from app.models.note import Note, note_schema, notes_schema
from app.notes import bp


@bp.route("/", methods=["GET"])
def list_notes():
    notes = dbase.session.query(Note).all()
    return notes_schema.dump(notes)


@bp.route("/", methods=["POST"])
def create_note():
    data = note_schema.load(request.get_json())
    note = Note(**data)
    dbase.session.add(note)
    dbase.session.commit()
    return note_schema.dump(note), 201
```

**4. Register the blueprint in `app/__init__.py`:**

```python
from app.main import bp as main_bp
from app.notes import bp as notes_bp

app.register_blueprint(main_bp)
app.register_blueprint(notes_bp)
```

**5. Verify it's wired up:**

```bash
uv run flask routes
```

You should see your new routes listed.

## Why the import happens at the *bottom* of `__init__.py`

```python
bp = Blueprint("notes", __name__, url_prefix="/notes")

from app.notes import routes  # noqa: E402,F401
```

`routes.py` needs to import `bp` from `app/notes/__init__.py` to register
routes on it (`@bp.route(...)`). If `app/notes/__init__.py` imported
`routes` at the *top* of the file — before `bp` is defined — you'd get a
circular import error. Defining `bp` first, then importing `routes` after,
breaks the cycle. This is a standard Flask blueprint idiom, not unique to
this project.

## Testing a new route

See [`testing.md`](testing.md) — in short, use the `client` fixture from
`tests/conftest.py`:

```python
def test_ping(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
```

## Rendering HTML instead of JSON

For routes that return a page rather than an API response, use
`render_template(...)`. If it's a simple static page (no forms, no DB
data), extend `index.html` instead of building the layout yourself — see
`app/templates/pages/about.html` for a working example, and
[`docs/templates.md`](templates.md) for the full templates guide.
