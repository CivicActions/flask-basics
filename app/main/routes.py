from flask import abort, render_template
from sqlalchemy import select

from app.extensions import dbase
from app.main import bp
from app.models.page import Page


@bp.route("/")
def home_page():
    return render_template("pages/home.html")


@bp.route("/about")
def about():
    return render_template("pages/about.html")


@bp.route("/p/<slug>")
def show_page(slug):
    page = dbase.session.execute(select(Page).filter_by(slug=slug)).scalar_one_or_none()
    if page is None:
        abort(404)
    return render_template("pages/dynamic.html", page=page)
