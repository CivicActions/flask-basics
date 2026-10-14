from flask import abort, render_template, flash, url_for, redirect
from flask_login import login_required
from sqlalchemy import select

from app.extensions import dbase
from app.main import bp
from app.models.post import Post
from app.forms.post_forms import PostForm


@bp.route("/")
def home_page():
    return render_template("pages/home.html")


@bp.route("/about")
def about():
    return render_template("pages/about.html")


@bp.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data)
        dbase.session.add(post)
        dbase.session.commit()
        flash("Post created!", "success")
        return redirect(url_for("main.show_page", slug=post.slug))
    return render_template("pages/post_form.html", form=form)


@bp.route("/post/<slug>")
def show_page(slug):
    page = dbase.session.execute(select(Post).filter_by(slug=slug)).scalar_one_or_none()
    if page is None:
        abort(404)
    return render_template("pages/post.html", page=page)
