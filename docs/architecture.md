# Architecture

This app uses the **application factory** pattern with **blueprints**, which
is the standard way to structure a Flask app that's going to grow beyond a
handful of routes. If you're new to Flask, read this before touching code —
it explains *why* the files are organized the way they are.

## Why a factory instead of a global `app = Flask(__name__)`?

The naive/tutorial way to write Flask is:

```python
# DON'T do this in a real project
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    ...
```

This works for a 10-line script, but breaks down for anything real:

1. **You can't create more than one app instance.** Tests need a fresh app
   configured differently (in-memory DB, `TESTING=True`) from the app you'd
   run in production. A global `app` object can't do that.
2. **Circular imports.** The moment your routes need the database, and the
   database needs the app, and the app needs the routes... you get import
   errors. The factory pattern breaks this cycle deliberately.

Instead, we define a **function** that builds and returns a configured app:

```python
# app/__init__.py
def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])
    dbase.init_app(app)
    app.register_blueprint(main_bp)
    return app
```

Anyone who needs an app — the dev server, the test suite, a future CLI
script — calls `create_app()` and gets a fully wired instance.

## The moving pieces

```
app/
├── __init__.py       # create_app() factory — the only place that assembles everything
├── config.py         # Config classes (Development/Testing/Production)
├── extensions.py     # Unbound extension instances (dbase, migrate) + the shared Base class
├── app.py            # Thin entrypoint: `app = create_app()`, used by `python app/app.py`
├── main/              # Example blueprint
│   ├── __init__.py    # Blueprint("main", __name__)
│   └── routes.py       # Routes registered on that blueprint
└── models/            # SQLAlchemy models — page.py is a real, working example
```

### `config.py`

Plain classes, one per environment. `create_app(config_name)` picks one by
name (`"development"`, `"testing"`, `"production"`, or `"default"`).
Nothing in here is Flask-specific — it's just data. See
[`configuration.md`](configuration.md) for details on env vars vs. config
classes.

### `extensions.py`

Extension objects (`dbase = SQLAlchemy(model_class=Base)`) are created
**without** an app attached, then bound later inside `create_app()` via
`.init_app(app)`.

This two-step "create unbound, bind later" pattern is the standard Flask
extension convention. It exists specifically so `extensions.py` doesn't need
to import `app/__init__.py` (which imports `extensions.py`) — i.e., it avoids
a circular import. Any new extension you add (e.g., a login manager, a mail
client) should follow the same pattern.

`extensions.py` also defines `Base(DeclarativeBase)` and passes it to
`SQLAlchemy(model_class=Base)`. Flask-SQLAlchemy's `dbase.Model` is assigned
dynamically at runtime, which mypy can't resolve as a base class — `Base` is
the same declarative base at runtime, but statically typed, so models should
subclass `Base` (see `app/models/base.py`), not `dbase.Model`.

### `main/` (blueprints)

A **blueprint** is a self-contained group of routes that gets registered onto
the app inside `create_app()`. Routes are *not* defined directly on the `app`
object anywhere except inside a blueprint. See
[`adding-routes.md`](adding-routes.md) for the full walkthrough.

### `app.py`

This is a thin wrapper, not the "real" app:

```python
from app import create_app
app = create_app()
```

It exists so you have something to point a WSGI server or `python app/app.py`
at. All the actual construction logic lives in the factory, not here.

## Request lifecycle, in one sentence

`create_app()` builds the app once at startup → Flask routes an incoming
request to the matching blueprint route function → that function talks to
`dbase.session` (SQLAlchemy) to read/write data → the route renders a Jinja
template with the model instance directly → returns a response.

Schema changes (adding/altering a model) go through **Flask-Migrate/Alembic**
(`migrations/`), not `dbase.create_all()` — see [`database.md`](database.md)
for the migration workflow.
