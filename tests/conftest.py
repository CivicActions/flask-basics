import pytest

from app import create_app
from app.extensions import dbase as _db


@pytest.fixture()
def app():
    """Flask app configured for testing (in-memory sqlite, TESTING=True)."""
    app = create_app("testing")
    yield app


@pytest.fixture()
def client(app):
    """Test client for making requests against the app without a live server."""
    return app.test_client()


@pytest.fixture()
def db(app):
    """DB session bound to the app context, rolled back after each test."""
    with app.app_context():
        yield _db
        _db.session.rollback()
