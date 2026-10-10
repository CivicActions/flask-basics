import os
from datetime import datetime, timezone

from flask import Flask

from app.config import config
from app.extensions import csrf, dbase, login_manager, migrate, oauth


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # Ensure the instance folder exists so the default sqlite file can be created.
    os.makedirs(app.instance_path, exist_ok=True)

    dbase.init_app(app)
    migrate.init_app(app, dbase)
    login_manager.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)
    # Authlib reads GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET from app.config
    # (it looks up "<NAME>_CLIENT_ID"), and discovers Google's endpoints and
    # signing keys from the OpenID Connect metadata URL on first use.
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    from app.main import bp as main_bp
    from app.routes.auth_routes import bp as auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

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
