from urllib.parse import urlsplit

from authlib.integrations.base_client import OAuthError
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user

from app.extensions import oauth
from app.forms.auth_forms import LogoutForm
from app.services.users_service import upsert_from_google

bp = Blueprint("auth", __name__)

# Session key holding where to send the user after the Google round-trip.
NEXT_URL_KEY = "login_next"


def is_safe_redirect(target: str | None) -> bool:
    """True only for same-site relative paths like "/post/hello".

    Rejects absolute URLs ("https://evil.example") and scheme-relative ones
    ("//evil.example", "/\\evil.example"), which browsers treat as off-site —
    otherwise `?next=` would be an open redirect.
    """
    if not target or not target.startswith("/") or target.startswith(("//", "/\\")):
        return False
    parts = urlsplit(target)
    return not parts.scheme and not parts.netloc


@bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home_page"))
    return render_template(
        "pages/login.html",
        next=request.args.get("next", ""),
        google_configured=bool(current_app.config["GOOGLE_CLIENT_ID"]),
    )


@bp.route("/login/google")
def login_google():
    """Start the OAuth flow: redirect the browser to Google's consent screen."""
    if not current_app.config["GOOGLE_CLIENT_ID"]:
        abort(503, "Google sign-in is not configured (set GOOGLE_CLIENT_ID).")

    next_url = request.args.get("next")
    session[NEXT_URL_KEY] = next_url if is_safe_redirect(next_url) else None

    # Must exactly match an "Authorized redirect URI" on the Google client.
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route("/auth/google/callback")
def google_callback():
    """Google redirects back here with an authorization code.

    authorize_access_token() verifies the `state` param (CSRF for the OAuth
    flow), swaps the code for tokens, and validates the signed ID token —
    its claims come back as token["userinfo"].
    """
    try:
        token = oauth.google.authorize_access_token()
    except OAuthError as exc:
        current_app.logger.warning("Google OAuth failed: %s", exc)
        flash("Google sign-in failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email_verified"):
        flash("Your Google account's email address must be verified.", "error")
        return redirect(url_for("auth.login"))

    user = upsert_from_google(userinfo)
    login_user(user)
    flash(f"Signed in as {user.email}.", "success")

    next_url = session.pop(NEXT_URL_KEY, None)
    if not is_safe_redirect(next_url):
        next_url = url_for("main.home_page")
    return redirect(next_url)


@bp.route("/logout", methods=["POST"])
def logout():
    form = LogoutForm()
    if not form.validate_on_submit():
        abort(400)
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.home_page"))


@bp.app_context_processor
def inject_logout_form():
    # The nav (partials/nav.html) renders a logout button on every page.
    return {"logout_form": LogoutForm()}
