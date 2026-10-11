# Authentication (Flask-Login + Google sign-in)

Users sign in with their Google account. Two libraries split the work:

- **[Authlib](https://docs.authlib.org/en/latest/client/flask.html)** handles the OAuth 2.0 / OpenID Connect
  round-trip with Google and verifies who the user is.
- **[Flask-Login](https://flask-login.readthedocs.io/)** remembers that user across requests (stores their id in
  the signed session cookie, reloads them via `user_loader`, provides `current_user` and `@login_required`).

There are no passwords stored anywhere in this app.

## Setup

1. In [Google Cloud Console](https://console.cloud.google.com/apis/credentials), create an **OAuth client ID** of
   type **Web application**.
2. Add `http://127.0.0.1:5000/auth/google/callback` as an **Authorized redirect URI** (add your real domain's
   equivalent for any deployed environment). It must match exactly, including host — `localhost` and `127.0.0.1`
   are different as far as Google is concerned.
3. Put the credentials in `.env`:

   ```
   GOOGLE_CLIENT_ID=....apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=...
   ```

4. `uv run flask db upgrade` (creates the `users` table) and `uv run flask run`.

`GOOGLE_API_KEY` is a different credential (for calling Google APIs like Maps) and is **not** used for sign-in.

## The flow

```
/login  ──"Sign in with Google"──>  /login/google  ──302──>  Google consent screen
                                                                   │
/  (or ?next=)  <──login_user()──  /auth/google/callback  <──302───┘
```

1. **`/login`** (`auth.login`) — the page Flask-Login redirects to from any `@login_required` view, with the
   original URL as `?next=`.
2. **`/login/google`** — stores `next` in the session (only if it's a safe, same-site path) and redirects to
   Google with a random `state` value.
3. **`/auth/google/callback`** — Authlib checks `state`, exchanges the code for tokens, and validates Google's signed
   ID token. Its claims (`sub`, `email`, `email_verified`, `name`, `picture`) are passed to
   `users_service.upsert_from_google()`, which creates or updates the `User`. Unverified emails are rejected. Then
   `login_user(user)` starts the session.
4. **`/logout`** — `POST` only, with a CSRF token (the nav renders it as a small form). A `GET` logout link could be
   triggered by any other site embedding `<img src=".../logout">`.

Users are identified by Google's `sub` claim, not by email: an account's email address can change, `sub` never does.

## Protecting a route

```python
from flask_login import current_user, login_required

@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("pages/dashboard.html", user=current_user)
```

`current_user` is also available in every template (`{% if current_user.is_authenticated %}`).

## Testing

`tests/test_auth.py` never talks to Google: it monkeypatches `oauth.google.authorize_access_token` to return fake
claims, then calls the callback route directly. To test a protected route, sign in the same way (see the `sign_in`
helper there) before making requests with the same `client`.

## Related pieces

- `CSRFProtect` is enabled app-wide (`app/extensions.py`); `TestingConfig` sets `WTF_CSRF_ENABLED = False`.
- `?next=` is validated by `is_safe_redirect()` in `app/routes/auth_routes.py` to avoid an open redirect.
