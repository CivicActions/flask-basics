from app.models.post import Post
from tests.test_auth import sign_in


def test_new_post_requires_login(client):
    response = client.get("/post/new")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_new_post_form_renders_when_logged_in(client, db, fake_google):
    sign_in(client)

    response = client.get("/post/new")
    assert response.status_code == 200
    assert "New Post" in response.text


def new_post_creates_post_and_redirect(client, db, fake_google):
    sign_in(client)

    response = client.post(
        "/post/new", data={"title": "Hello There!", "body": "<p>First Post</p>"}
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/post/hello-there"
    post = db.session.query(Post).one()
    assert post.title == "Hello There!"


def test_new_post_rejects_empty_form(client, db, fake_google):
    sign_in(client)
    response = client.post("/post/new", data={"title": "", "body": ""})
    assert response.status_code == 200
    assert db.session.query(Post).count() == 0
