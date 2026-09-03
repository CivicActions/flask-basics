import os
from datetime import datetime, timezone

from flask import Flask

from app.config import config
from app.extensions import dbase, marsh, migrate


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # Ensure the instance folder exists so the default sqlite file can be created.
    os.makedirs(app.instance_path, exist_ok=True)

    # Order matters: SQLAlchemy must be initialized before Marshmallow so
    # flask-marshmallow's SQLAlchemy integration (SQLAlchemyAutoSchema) works.
    dbase.init_app(app)
    marsh.init_app(app)
    migrate.init_app(app, dbase)

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_globals():
        # Makes `current_year` available in every template without each
        # view having to pass it explicitly (used in partials/footer.html).
        return {"current_year": datetime.now(timezone.utc).year}

    with app.app_context():
        from app import models  # noqa: F401  (registers models on db.metadata)

        # Schema changes in dev/production go through Flask-Migrate/Alembic
        # (see `flask db migrate` / `flask db upgrade`, docs/database.md).
        # Tests use a throwaway in-memory db, so create_all() is fine there —
        # there's no migration history to maintain for a db that's discarded
        # after every test run.
        if app.config.get("TESTING"):
            dbase.create_all()

    return app
