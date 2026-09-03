# Testing

Tests live in `tests/`, use `pytest`, and rely on shared fixtures defined in
`tests/conftest.py`. Run the whole suite with:

```bash
uv run pytest
```

Run one file, or one test, with:

```bash
uv run pytest tests/test_routes.py
uv run pytest tests/test_routes.py::test_index_returns_hello_world
```

Add `-v` for verbose output, or `--cov=app` (via `pytest-cov`, already a dev
dependency) to see coverage:

```bash
uv run pytest --cov=app --cov-report=term-missing
```

## The fixtures (`tests/conftest.py`)

| Fixture | What it gives you |
|---|---|
| `app` | A Flask app built with `create_app("testing")` — in-memory SQLite, `TESTING=True`. Fresh instance per test. |
| `client` | `app.test_client()` — use this to make fake HTTP requests without a running server. |
| `db` | The shared `db` object, used inside `app`'s app context, rolled back after the test. |

Every fixture is **function-scoped** (a new one per test) unless you
explicitly change that — this is what keeps tests from silently affecting
each other.

## Testing a route

```python
def test_index_returns_hello_world(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"Hello World!"
```

Use `client`, not `app`, whenever you're testing HTTP behavior — it goes
through Flask's real request/response cycle (headers, status codes,
URL routing) instead of calling view functions directly.

## Testing something that touches the database

```python
def test_create_note(client, db):
    response = client.post("/notes/", json={"title": "hello"})
    assert response.status_code == 201

    from app.models.note import Note
    assert db.session.query(Note).count() == 1
```

## ⚠️ The #1 gotcha: don't define models inside test functions

`db.Model` / `db.metadata` are **shared, process-global objects** on the
single `db` instance from `app/extensions.py`. They are *not* reset between
tests, and not scoped per-`app` fixture.

If you define a model class inside a test function:

```python
def test_something(app, db):
    class Widget(db.Model):        # DON'T do this
        __tablename__ = "widgets"
        ...
```

...that class registration is **permanent for the rest of the pytest
session**. Every subsequent `create_app()` call (which every `app` fixture
does) will call `db.create_all()` and recreate that table — even in tests
that have nothing to do with widgets. This was verified directly while
building this test suite; see the git history / `tests/test_db.py` for the
real example of the leak and the fix.

**The fix:** define ad-hoc/test-only models once, at **module scope** (top
of the test file, outside any function):

```python
from app.extensions import dbase


class Widget(dbase.Model):
    __tablename__ = "widgets"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


def test_one(app, db):
    ...


def test_two(app, db):
    ...
```

This is only relevant for throwaway/ad-hoc test models. Real models (in
`app/models/`) are already defined exactly once, at import time, so this
doesn't apply to them — just don't redefine a real model's class anywhere
else.

## What *is* isolated between tests

Even though schema (tables) can leak via shared metadata as described above,
**data does not** — each `app` fixture creates a fresh `create_app("testing")`
call, which gets its own separate in-memory SQLite database/engine. A row
inserted in one test is never visible in another test's `db` fixture.

## Naming and organization conventions

- One test file per module/concern: `test_routes.py`, `test_db.py`,
  `test_app_factory.py`. As you add blueprints/models, add matching test
  files (`test_notes.py`, etc.) rather than growing one giant file.
- Test function names should describe the behavior being verified, not the
  implementation: `test_index_returns_hello_world`, not `test_bp_route_1`.
- Don't reach for mocks/patches to avoid the database — the in-memory
  SQLite `testing` config is fast enough that you don't need to.
