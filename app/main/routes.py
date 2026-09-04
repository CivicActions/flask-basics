from flask import abort, render_template
from sqlalchemy import select

from app.extensions import dbase
from app.main import bp
from app.models.post import Post


@bp.route("/")
def home_page():
    return render_template("pages/home.html")


@bp.route("/about")
def about():
    return render_template("pages/about.html")


@bp.route("/post/<slug>")
def show_page(slug):
    page = dbase.session.execute(select(Post).filter_by(slug=slug)).scalar_one_or_none()
    if page is None:
        abort(404)
    return render_template("pages/post.html", page=page)
