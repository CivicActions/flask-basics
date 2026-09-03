# Templates

Templates live in `app/templates/` and use Jinja2 (bundled with Flask).
Styling is [Tailwind CSS](https://tailwindcss.com/), loaded via the **Play
CDN** script tag — there's no Node/npm build step in this project.

```
app/templates/
├── base.html            # site-wide layout: <html>, nav, footer, main content block
├── page.html             # extends base.html; layout for simple static pages
├── partials/
│   ├── nav.html           # top navigation bar
│   └── footer.html         # site footer
└── pages/
    ├── about.html          # hardcoded static page (extends page.html)
    └── dynamic.html         # renders a DB-backed Page model (extends page.html)
```

## `base.html` — the site-wide layout

Every page in the app ultimately extends this template (usually indirectly,
via `index.html`). It defines the `<html>`/`<head>`/`<body>` skeleton, pulls
in Tailwind, includes the nav and footer partials, and exposes these blocks
for child templates to override:

| Block | Purpose |
|---|---|
| `title` | `<title>` tag content |
| `head` | Extra `<head>` content (e.g. a page-specific `<meta>` tag) |
| `content` | The main page body |
| `scripts` | Extra `<script>` tags, placed at the end of `<body>` |

A route that needs full control over its layout (a dashboard, a form page,
etc.) should extend `base.html` directly:

```jinja
{% extends "base.html" %}
{% block title %}Dashboard - Hootenanny{% endblock %}
{% block content %}
    <h1>Dashboard</h1>
    ...
{% endblock %}
```

## `partials/nav.html` and `partials/footer.html`

These are pulled into `base.html` with `{% include %}`, not `{% extends %}`
— they're not standalone pages, just reusable fragments. Keeping them in
their own files means:

- You only update the nav/footer markup in one place.
- `base.html` stays readable instead of being 100+ lines long.

If you add a new top-level page (see `adding-routes.md`), add a link to it
in `partials/nav.html`:

```jinja
<a href="{{ url_for('main.about') }}" class="hover:text-gray-900">About</a>
```

Always use `url_for(...)`, never a hardcoded `href="/about"` — it keeps
links correct if a route's path or blueprint ever changes.

The footer uses a `current_year` variable — this comes from a
`@app.context_processor` registered in `create_app()` (in `app/__init__.py`),
which makes it available in *every* template automatically without each view
function passing it in.

## `index.html` — the template for static pages

Most "static" pages (About, Terms, Contact — pages that are just fixed
content, no forms or database queries) don't need to redefine the whole
layout. They extend `index.html` instead of `base.html`:

```jinja
{% extends "page.html" %}
{% set page_title = "About" %}

{% block page_content %}
    <p>Your content here.</p>
{% endblock %}
```

`index.html` itself extends `base.html` and adds a consistent heading +
reading-width container around whatever you put in `page_content`. This
means every static page automatically looks consistent (same heading size,
same max-width) without copy-pasting that markup into each one.

**Rule of thumb:**
- Static/simple content (even if fetched from the database, as long as the
  *template* itself has no forms or complex conditional layout) → extend
  `index.html`. `pages/dynamic.html` is a good example: the route queries the
  database, but the template just drops the result into `index.html`'s
  container.
- Anything with a form, multiple content regions, or a layout that doesn't
  fit a single heading + article block → extend `base.html` directly instead.

See `app/templates/pages/about.html` (hardcoded content) and
`app/templates/pages/dynamic.html` (renders a `Page` model row) — both used
by routes in `app/main/routes.py` — for complete, working examples.

## Adding a new static page

1. Create `app/templates/pages/<name>.html`, extending `index.html` (copy
   `about.html` as a starting point for hardcoded content, or
   `dynamic.html` if it should pull content from the database).
2. Add a route that renders it — see
   [`adding-routes.md`](adding-routes.md):
   ```python
   @bp.route("/terms")
   def terms():
       return render_template("pages/terms.html")
   ```
3. Add a link to it in `partials/nav.html` if it should be reachable from
   the nav.
4. Add a test asserting the route returns 200 and contains expected content
   (see `tests/test_routes.py`).

## Tailwind CSS — current setup and its limits

Tailwind is loaded via `<script src="https://cdn.tailwindcss.com">` in
`base.html`. This is the **Play CDN** build — it compiles all of Tailwind's
utility classes in the browser, on every page load, using JavaScript.

This is fine for this project's current size, but it's explicitly **not**
recommended by Tailwind for production use — it's slower (JS has to run
before styles apply) and ships far more CSS-generation code than a real app
needs.

**If/when this project needs the real build:**

```bash
npm install -D tailwindcss
npx tailwindcss init
# configure content: ["./app/templates/**/*.html"] in tailwind.config.js
npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/tailwind.css --watch
```

Then replace the `<script src="https://cdn.tailwindcss.com">` tag in
`base.html` with a normal `<link rel="stylesheet" href="{{ url_for('static', filename='css/tailwind.css') }}">`
tag. This isn't done yet — it's a good next step once this project needs a
real Node build step, but adds tooling (`npm`, a `tailwind.config.js`, a
watch process) that isn't worth it for a handful of pages.

## `static/css/custom.css`

An empty stylesheet, linked in `base.html`, reserved for any CSS that
genuinely can't be expressed as Tailwind utility classes (rare — reach for a
utility class first).
