# Forms (WTForms / Flask-WTF)

This doc explains what WTForms/Flask-WTF are, why they're here, and how to actually wire them in.

## What WTForms and Flask-WTF actually are

- **[WTForms](https://wtforms.readthedocs.io/)** is a form library: you declare a form as a Python class (fields + validators), and it handles
  parsing submitted data, running validation, and reporting errors per field. It has no Flask dependency at all —
  it works with any framework.
- **[Flask-WTF](https://flask-wtf.readthedocs.io/)** is a thin integration layer on top of WTForms for Flask specifically. It adds:
  - Automatic **CSRF protection** on every form (a hidden token field + verification on submit).
  - A `FlaskForm` base class that reads submitted data from `request.form`/`request.files` automatically, instead
    of you wiring that up by hand.

In short: WTForms defines *what a form looks like and how it validates*; Flask-WTF handles *getting request data
into it safely* in a Flask app.

## Why use this instead of just reading `request.form` directly?

You could read `request.form["title"]` in a view function and validate it by hand. WTForms is worth the extra
layer once you have more than a field or two, because it gives you for free:
- **Validation with reusable rules** (`DataRequired`, `Length`, `Email`, etc.) instead of a pile of `if`
  statements.
- **CSRF protection** — without it, any HTML page hosted elsewhere could submit a POST to your app on a logged-in
  user's behalf. This matters the moment you have any state-changing POST route.
- **Re-rendering a form with its previous values and per-field errors** after a failed submission, instead of
  losing what the user typed.

## Prerequisite: enable CSRF protection app-wide

`flask-wtf` being installed does **not** automatically protect anything — `CSRFProtect` has to be initialized.
This project doesn't do that yet. Following the pattern in `app/extensions.py` (shared, unbound extension
instances, bound later via `init_app`):

**1. Add it to `app/extensions.py`:**

```python
from flask_wtf import CSRFProtect

csrf = CSRFProtect()
```

**2. Bind it in `create_app()` (`app/__init__.py`), alongside `dbase`/`migrate`:**

```python
from app.extensions import csrf, dbase, migrate

csrf.init_app(app)
```

`SECRET_KEY` (already set in `app/config.py`) is what Flask-WTF uses to sign CSRF tokens — it's the same key
used for sessions. Note the README's existing warning: the `"dev"` default is fine locally but must be overridden
via `.env` before this is ever exposed beyond your machine.

## Example: a form for the existing `Post` model

Using `app/models/post.py` (`slug`, `title`, `body`) as the concrete example:

**1. Create `app/main/forms.py`:**

```python
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp

class PostForm(FlaskForm):
    slug = StringField(
        "Slug",
        validators=[
            DataRequired(),
            Length(max=80),
            Regexp(r"^[a-z0-9-]+$", message="Use lowercase letters, numbers, and hyphens only."),
        ],
    )
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    body = TextAreaField("Body", validators=[DataRequired()])
```

Field lengths/constraints mirror the column definitions in `Post` — keep these two in sync when either changes.

**2. Use it in a route (`app/main/routes.py`):**

```python
from app.main.forms import PostForm

@bp.route("/post/new", methods=["GET", "POST"])
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(slug=form.slug.data, title=form.title.data, body=form.body.data)
        dbase.session.add(post)
        dbase.session.commit()
        return redirect(url_for("main.show_page", slug=post.slug))
    return render_template("pages/post_form.html", form=form)
```

`validate_on_submit()` does two things in one call: confirms the request is a `POST`, and runs all field
validators. On `GET` (or a failed `POST`), it's `False` and you fall through to re-rendering the form — with
whatever the user already typed still in `form.<field>.data`, and errors available at `form.<field>.errors`.

**3. Render it in a template (`app/templates/pages/post_form.html`)**, extending `base.html` per
[`docs/templates.md`](templates.md):

```html
{% extends "base.html" %}
{% block content %}
<form method="post" novalidate>
    {{ form.csrf_token }}

    {{ form.slug.label }} {{ form.slug() }}
    {% for error in form.slug.errors %}<p class="text-red-600">{{ error }}</p>{% endfor %}

    {{ form.title.label }} {{ form.title() }}
    {% for error in form.title.errors %}<p class="text-red-600">{{ error }}</p>{% endfor %}

    {{ form.body.label }} {{ form.body() }}
    {% for error in form.body.errors %}<p class="text-red-600">{{ error }}</p>{% endfor %}

    <button type="submit">Save</button>
</form>
{% endblock %}
```

`{{ form.csrf_token }}` renders the hidden CSRF input — without it, every `POST` through this form will be
rejected once `CSRFProtect` is enabled.

## Testing a form-backed route

Following the pattern in [`docs/testing.md`](testing.md) (use the `client` fixture), POST form-encoded data,
not JSON:

```python
def test_new_post_creates_page(client):
    response = client.post(
        "/post/new",
        data={"slug": "hello", "title": "Hello", "body": "<p>Hi</p>"},
        follow_redirects=True,
    )
    assert response.status_code == 200
```

`client.post(data=...)` sends `application/x-www-form-urlencoded`, which is what `FlaskForm` expects. Since
`TestingConfig` doesn't disable CSRF, the test client still needs a valid token for this to pass once
`CSRFProtect` is enabled — either fetch the form's `GET` page first and extract the  token, or set
`WTF_CSRF_ENABLED = False` on `TestingConfig` specifically (common practice: keep CSRF on in dev/production, off
in tests, since tests already run same-origin and aren't exercising the CSRF threat model).

## Common mistakes to avoid

- **Forgetting `csrf.init_app(app)`** — `FlaskForm` will still work, but CSRF tokens won't actually be verified,
  silently defeating the point.
- **Forgetting `{{ form.csrf_token }}` in the template** — once CSRF *is* enabled, every submit will fail with
  a 400 until this is added.
- **Validating with `form.validate()` alone instead of `validate_on_submit()`** — `validate()` doesn't check the
  request method, so a `GET` request could accidentally look "submitted" if fields happen to be prefilled.
- **Re-declaring field constraints that drift from the model.** If `Post.slug` changes its max length, update
  `PostForm.slug`'s `Length` validator too — nothing keeps them in sync automatically.
