from marshmallow import ValidationError
import pytest

from app.models.page import Page, page_schema


def test_page_model_create_query(db):
    db.session.add(Page(slug="hello", title="Hello", body="<p>Hi</p>"))
    db.session.commit()

    page = db.session.query(Page).filter_by(slug="hello").first()
    assert page is not None
    assert page.title == "Hello"
    assert page.created_at is not None


def test_page_schema_dump(db):
    page = Page(slug="about-us", title="About Us", body="<p>Content</p>")
    db.session.add(page)
    db.session.commit()

    data = page_schema.dump(page)
    assert data["slug"] == "about-us"
    assert data["title"] == "About Us"
    assert "id" in data


def test_page_schema_rejects_invalid_slug(db):
    with pytest.raises(ValidationError):
        page_schema.load({"slug": "Not A Valid Slug!", "title": "x", "body": ""})


def test_show_page_route_returns_200(client, db):
    db.session.add(Page(slug="hello", title="Hello Page", body="<p>Body text</p>"))
    db.session.commit()

    response = client.get("/p/hello")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Hello Page" in body
    assert "Body text" in body
    # rendered via index.html, which pulls in base.html's nav/footer
    assert "<nav" in body


def test_show_page_route_404_for_missing_slug(client):
    response = client.get("/p/does-not-exist")
    assert response.status_code == 404
