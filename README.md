# Hootenanny

A Flask application for coordinating the CA's Summit Hootenanny.This README (and the docs it links to) is meant to
explain not just *what* to run, but *why* the project is structured the way it is.

## Stack

- **[Flask](https://flask.palletsprojects.com/)** — web framework
- **[SQLAlchemy](https://www.sqlalchemy.org/)** (via Flask-SQLAlchemy) — ORM / database access
- **[Flask-Migrate](https://flask-migrate.readthedocs.io/)** (Alembic) — database schema migrations
- **[Marshmallow](https://marshmallow.readthedocs.io/)** + **[flask-marshmallow](https://flask-marshmallow.readthedocs.io/)** + **marshmallow-sqlalchemy** — request/response validation and serialization
- **[Flask-WTF](https://flask-wtf.readthedocs.io/)** — HTML form handling/CSRF
- **[pytest](https://docs.pytest.org/)** — test runner
- **[uv](https://docs.astral.sh/uv/)** — dependency management + running commands (this repo does not use plain `pip`/`venv` directly)
- **SQLite** — the database, for now (see [`docs/database.md`](docs/database.md))

If you don't know one of these tools yet, that's the point of this
project — look it up as you go.

## Quick start

**Prerequisites:** [`uv`](https://docs.astral.sh/uv/getting-started/installation/) which is already installed on your CA laptop. That's it — `uv` manages the Python
version and virtual environment for you.

```bash
# Install dependencies (creates .venv/ automatically)
uv sync

# Apply database migrations (creates instance/app.db with all tables)
uv run flask db upgrade

# Run the dev server
uv run flask run
# -> visit http://127.0.0.1:5000/

# Run the tests
uv run pytest
```

Every command in this repo is prefixed with `uv run` instead of activating a virtualenv manually — `uv run` finds/uses
the project's `.venv` automatically. See [uv's docs](https://docs.astral.sh/uv/) if this is new
to you.

### Useful commands

```bash
uv run flask routes          # list every registered route
uv run flask shell            # open a Python shell with app context loaded
uv run flask db migrate -m "message"   # generate a migration after changing a model
uv run flask db upgrade                 # apply pending migrations
uv run pytest -v               # verbose test output
uv run pytest --cov=app --cov-report=term-missing   # test coverage report
uv add <package>               # add a new dependency (updates pyproject.toml + uv.lock)
```

## Project structure

```
.
├── app/
│   ├── __init__.py       # create_app() — the application factory
│   ├── app.py             # thin entrypoint: app = create_app()
│   ├── config.py          # Config classes (Development/Testing/Production)
│   ├── extensions.py      # Shared, unbound extension instances (db, ma, migrate)
│   ├── main/               # example blueprint (routes grouped by feature)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models/             # SQLAlchemy models — one file per model (page.py is a real example)
│   ├── static/
│   └── templates/
├── tests/
│   ├── conftest.py         # shared pytest fixtures (app, client, db)
│   ├── test_app_factory.py
│   ├── test_db.py
│   ├── test_page_model.py
│   └── test_routes.py
├── migrations/              # Alembic migration history (via Flask-Migrate) — committed to git
│   └── versions/
├── instance/                 # gitignored; holds the local instance/app.db sqlite file
├── .env                      # gitignored; secrets/local overrides (currently empty)
├── .flaskenv                 # committed; tells the `flask` CLI how to find/run the app
├── pyproject.toml
└── docs/                     # deep-dive guides — see below
```

## Documentation

This README covers the basics. For anything more involved, see the guides
in [`docs/`](./docs/):

| Guide                                            | What's in it                                                                                                |
|--------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| [`docs/architecture.md`](docs/architecture.md)   | Why the app factory + blueprint pattern is used, and how the pieces fit together                            |
| [`docs/configuration.md`](docs/configuration.md) | `.env` vs `.flaskenv` vs `config.py` — what goes where and why                                              |
| [`docs/adding-routes.md`](docs/adding-routes.md) | How to add a route to an existing blueprint, or create a new one                                            |
| [`docs/templates.md`](docs/templates.md)         | Base layout, nav/footer partials, and how the static-page template works                                    |
| [`docs/adding-models.md`](docs/adding-models.md) | How to add a SQLAlchemy model (and a Marshmallow schema for it)                                             |
| [`docs/database.md`](docs/database.md)           | Where the DB lives per environment, and the Flask-Migrate/Alembic workflow for schema changes               |
| [`docs/testing.md`](docs/testing.md)             | How to write tests, the fixtures available, and a real gotcha about shared SQLAlchemy metadata across tests |

**If you only read one doc, read `docs/architecture.md` first** — it explains the app factory pattern that everything
else assumes you already understand.

## Contributing / making changes

Rough workflow for adding a feature end-to-end:

1. Add a model — [`docs/adding-models.md`](docs/adding-models.md)
2. Add a route (in an existing or new blueprint) — [`docs/adding-routes.md`](docs/adding-routes.md)
3. Add tests for both — [`docs/testing.md`](docs/testing.md)
4. Run `uv run pytest` before considering it done

Before committing your work, run `uv run pre-commit install` once (this also installs the commit-msg hook — see below).
After that, the hooks in [`.pre-commit-config.yaml`](.pre-commit-config.yaml) run automatically on every commit:
[ruff](https://docs.astral.sh/ruff/) (lint + format),
[mypy](https://mypy-lang.org/) (type checking), [bandit](https://bandit.readthedocs.io/en/latest/)
(security linting), [pip-audit](https://pypi.org/project/pip-audit/) (dependency vulnerability scanning), and some
general file format checkers. `pre-commit` and `commitizen` are both installed automatically via `uv sync`
(they're in the `dev` dependency group) — no separate global install needed.

### Commit messages: Commitizen + Conventional Commits

This repo enforces [Conventional Commits](https://www.conventionalcommits.org/) formatted commit messages, via
[Commitizen](https://commitizen-tools.github.io/commitizen/) running as a `commit-msg` hook. Once you've run
`pre-commit install`, any commit whose message doesn't match the required format is **rejected**:

```
<type>(<optional scope>): <description>
```

Allowed `<type>` values: `feat`, `fix`, `build`, `bump`, `chore`, `ci`, `docs`, `perf`, `refactor`, `revert`, `style`,
`test`.

```bash
git commit -m "feat: add page model and dynamic page route"
git commit -m "fix(routes): return 404 for missing page slug"
git commit -m "not following the format"   # rejected by the commit-msg hook
```

If you'd rather not memorize the format, use Commitizen's interactive prompt instead of `git commit` directly — it asks
you for the type, scope, and description and builds a compliant message for you:

```bash
uv run cz commit
```

**Why this matters beyond style:** Conventional Commits is what makes automated changelog generation and semantic
version bumping possible later (`cz bump`, `cz changelog`) — the commit history itself becomes structured data instead
of free text.


## Known gaps / honest state of this project

This is a real, working app, not a polished one. Things intentionally left unfinished as learning opportunities / next
steps:

- **`SECRET_KEY` defaults to `"dev"`** if `.env` doesn't set one — fine for local development, not fine for anything
  production.
- **Only one blueprint (`main`) and one real model (`Page`)** — a good next exercise is adding a second model/blueprint
  pair following the same pattern (see [`docs/adding-models.md`](docs/adding-models.md) and
  [`docs/adding-routes.md`](docs/adding-routes.md)).
- **`Page.body` is rendered with Jinja's `|safe` filter** (raw HTML, no escaping) — fine for trusted/admin-authored
  content, a real risk if this ever accepts page content from untrusted users without sanitization. See the note in
  `app/templates/pages/dynamic.html`.
- **No admin UI for creating `Page` rows** — pages are currently created via `flask shell` or a script; a form-based
  create/edit route (Flask-WTF is already a dependency for this) is a natural next feature.
