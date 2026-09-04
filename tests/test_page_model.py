from app.models.post import Post


def test_page_model_create_query(db):
    db.session.add(Post(slug="hello", title="Hello", body="<p>Hi</p>"))
    db.session.commit()

    page = db.session.query(Post).filter_by(slug="hello").first()
    assert page is not None
    assert page.title == "Hello"
    assert page.created_at is not None


def test_show_page_route_returns_200(client, db):
    db.session.add(Post(slug="hello", title="Hello Page", body="<p>Body text</p>"))
    db.session.commit()

    response = client.get("/post/hello")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Hello Page" in body
    assert "Body text" in body
    # rendered via index.html, which pulls in base.html's nav/footer
    assert "<nav" in body


def test_show_page_route_404_for_missing_slug(client):
    response = client.get("/post/does-not-exist")
    assert response.status_code == 404
