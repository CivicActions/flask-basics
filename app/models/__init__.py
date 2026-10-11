# Import model modules here so they register with SQLAlchemy's metadata
# when this package is imported (see create_app() in app/__init__.py).
from app.models.post import Post  # noqa: F401
from app.models.users import User  # noqa: F401
