import pytest
from authlib.integrations.base_client import OAuthError

from app.extensions import oauth
from app.models.users import User, load_user
from app.routes.auth_routes import is_safe_redirect

GOOGLE_USERINFO = {
    "sub": "google-123",
    "email": "Ada@Example.com",
    "email_verified": True,
    "name": "Ada Lovelace",
    "picture": "https://example.com/ada.png",
}


@pytest.fixture()
def google_configured(app):
    app.config["GOOGLE_CLIENT_ID"] = "test-client-id"
    app.config["GOOGLE_CLIENT_SECRET"] = "test-client-secret"


@pytest.fixture()
def fake_google(monkeypatch):
    """Replace the network-facing parts of the Google OAuth client.

    Returns a dict the test can edit to change what Google "sends back".
    """
    response = {"userinfo": dict(GOOGLE_USERINFO)}

    def authorize_access_token(**kwargs):
        if "error" in response:
            raise OAuthError(error=response["error"])
        return response

    monkeypatch.setattr(oauth.google, "authorize_access_token", authorize_access_token)
    return response


def sign_in(client, next_url=None):
    if next_url:
        with client.session_transaction() as sess:
            sess["login_next"] = next_url
    return client.get("/auth/google/callback")


def test_login_page_renders(client, google_configured):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sign in with Google" in response.text


def test_login_page_explains_missing_config(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "GOOGLE_CLIENT_ID" in response.text


def test_login_google_503_when_unconfigured(client):
    assert client.get("/login/google").status_code == 503


def test_login_google_stores_only_safe_next(client, monkeypatch, google_configured):
    monkeypatch.setattr(
        oauth.google, "authorize_redirect", lambda uri: ("redirecting", 302)
    )

    client.get("/login/google?next=/about")
    with client.session_transaction() as sess:
        assert sess["login_next"] == "/about"

    client.get("/login/google?next=https://evil.example")
    with client.session_transaction() as sess:
        assert sess["login_next"] is None


def test_callback_creates_user_and_logs_in(client, db, fake_google):
    response = sign_in(client)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    user = db.session.query(User).one()
    assert user.google_sub == "google-123"
    assert user.email == "ada@example.com"
    assert user.last_login_at is not None
    with client.session_transaction() as sess:
        assert sess["_user_id"] == str(user.id)


def test_callback_updates_existing_user(client, db, fake_google):
    sign_in(client)
    fake_google["userinfo"]["name"] = "Countess Lovelace"
    sign_in(client)

    user = db.session.query(User).one()
    assert user.name == "Countess Lovelace"


def test_callback_redirects_to_stored_next(client, db, fake_google):
    response = sign_in(client, next_url="/about")
    assert response.headers["Location"] == "/about"


def test_callback_rejects_unverified_email(client, db, fake_google):
    fake_google["userinfo"]["email_verified"] = False

    response = sign_in(client)

    assert response.headers["Location"] == "/login"
    assert db.session.query(User).count() == 0


def test_callback_handles_oauth_error(client, db, fake_google):
    fake_google["error"] = "access_denied"

    response = sign_in(client)

    assert response.headers["Location"] == "/login"
    assert db.session.query(User).count() == 0


def test_nav_shows_user_when_logged_in(client, db, fake_google):
    sign_in(client)
    response = client.get("/")
    assert "Ada Lovelace" in response.text
    assert "Sign out" in response.text


def test_logout_requires_post(client):
    assert client.get("/logout").status_code == 405


def test_logout_clears_session(client, db, fake_google):
    sign_in(client)
    response = client.post("/logout")

    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert "_user_id" not in sess


def test_load_user(db, fake_google, client):
    sign_in(client)
    user = db.session.query(User).one()

    assert load_user(str(user.id)) == user
    assert load_user("999") is None
    assert load_user("not-an-id") is None


@pytest.mark.parametrize(
    "target, expected",
    [
        ("/about", True),
        ("/post/hello?x=1", True),
        (None, False),
        ("", False),
        ("about", False),
        ("https://evil.example", False),
        ("//evil.example", False),
        ("/\\evil.example", False),
    ],
)
def test_is_safe_redirect(target, expected):
    assert is_safe_redirect(target) is expected
