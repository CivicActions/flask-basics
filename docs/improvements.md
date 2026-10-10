# Possible Improvements / Open Tasks

This is a running list of known gaps, rough edges, and reasonable steps across the project — things that
are intentionally not fixed yet because they're either out of scope for a learning project, or good exercises
for whoever picks this up next. See also the "Known gaps / honest state of this project" section in the
top-level [README](../README.md) for the original set of these.

## `Post.slug` auto-generation (`app/models/post.py`)

Slugs are auto-generated from `title` via `python-slugify` when not supplied explicitly (a `before_insert` event
listener). This closes introduces some potential for problems:

- **No uniqueness collision handling.** Two posts with the same (or similarly-slugifying) title generate the same
  slug. `slug` is `unique=True`, so the second insert fails with an `IntegrityError` at commit time rather than
  being handled gracefully — e.g. by appending `-2`, a short random suffix, or the row's `id`. Whoever adds a real
  "create post" UI (see [`docs/forms.md`](forms.md)) will need to either handle this collision explicitly or
  catch/report the DB error cleanly instead of a raw 500.
- **Slug doesn't update if `title` changes later.** The listener only runs on `before_insert`, not `before_update`
  — by design, so that a post's URL doesn't silently change out from under anyone who's linked to it. But this is
  a one-sided decision that isn't documented anywhere for someone editing a post's title and expecting the slug to
  follow. If slug stability is the desired behavior long-term, it should be called out explicitly (e.g. in
  `docs/adding-models.md` or a comment on the listener itself); if it's not, a `before_update` listener (or an
  explicit "regenerate slug" action) would need to be added.
- **No normalization/validation beyond what `slugify()` does.** An empty or whitespace-only `title` slugifies to
  `""`, which would violate `nullable=False` at the DB level with a possibly-confusing error rather than a clear
  validation message. This is more of an issue once a form is in front of this model (see `docs/forms.md`'s
  `PostForm.slug` validators as a related, separate check that doesn't currently talk to this model-level generation
  at all).

## Forms / CSRF (`docs/forms.md`)

- ~~**`CSRFProtect` is not actually initialized anywhere.**~~ Done as part of Google sign-in (see
  [`docs/authentication.md`](authentication.md)); `TestingConfig` disables it.
- **No create/edit UI for `Post` exists.** Posts can currently only be created via `flask shell` or a script. A
  `PostForm` (per `docs/forms.md`) backing a real `/post/new` (and `/post/<slug>/edit`) route is the natural next
  feature — and now a good place to also solve the slug-collision problem above, since a form is where a duplicate
  title would first be user-visible.

## General / carried over from the README

- **`SECRET_KEY` defaults to `"dev"`.** Fine for local dev, must be set via `.env` before anything resembling a
  shared or production deployment — this also affects Flask-WTF's CSRF token signing once CSRF protection is enabled.
- **`Page.body` is rendered with Jinja's `|safe` filter** (raw HTML, no escaping). Fine while only
  trusted/admin-authored content goes into `Post.body`; becomes an XSS risk the moment any untrusted user can
  influence that field — worth revisiting together with the "add a create/edit UI" task above, since a form is exactly
  where untrusted input would start entering this field.
- **Only one blueprint (`main`) and one real model (`Post`)** — adding a second model/blueprint pair (see
  `docs/adding-models.md` and `docs/adding-routes.md`) remains a good exercise for exercising the full add-a-feature
  workflow end-to-end.

## Users / auth (`app/services/users_service.py`)

- **`create_user()` / `update_user()` predate Google sign-in** and don't fit the `User` model: `create_user()` never
  sets `google_sub` (non-nullable), so it fails with an `IntegrityError` that gets reported as `EmailAlreadyExists`;
  `update_user()` whitelists `is_active`, which is a read-only property from `UserMixin`. `email` also isn't unique,
  so `EmailAlreadyExists` can't actually fire. These are unused today — fix or remove before a users admin UI
  (`app/routes/users_routes.py` is still empty) builds on them.
- **No authorization.** Any Google account can sign in. Restricting by domain (Google's `hd` claim) or an allowlist,
  and/or an `is_admin` flag, would be needed before protecting anything sensitive behind `@login_required`.
