import os

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    # An empty/blank DATABASE_URL (as shipped in .env.example) means
    # "use the local SQLite default", not "use an empty URI".
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL", "").strip()
        or f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    FLASK_APP = os.environ.get("FLASK_APP", "app")
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", False)
    # OAuth 2.0 "Web application" client credentials from Google Cloud
    # Console (APIs & Services -> Credentials). Sign-in uses these, not
    # GOOGLE_API_KEY. See docs/authentication.md.
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Tests run same-origin and don't exercise the CSRF threat model
    # (see docs/forms.md).
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
