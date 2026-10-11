from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import dbase, login_manager
from app.models.base import BaseModel


class User(UserMixin, BaseModel):
    """An account created/updated on Google sign-in (see
    app/services/users_service.py:upsert_from_google).

    `UserMixin` supplies what Flask-Login needs (`is_authenticated`,
    `is_active`, `get_id()` -> `str(self.id)`), so nothing is overridden here.
    """

    __tablename__ = "users"

    # Google's stable, unique account identifier (the "sub" claim). Users are
    # matched on this, never on email — a Google account's email can change.
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    email: Mapped[str] = mapped_column(String(320), index=True)
    email_verified: Mapped[bool] = mapped_column(default=False)
    name: Mapped[str | None] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(String(2048))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email!r}>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Reload the user from the id Flask-Login stored in the session.

    Must return None (not raise) for an unknown id, e.g. a session cookie
    that outlived its user — Flask-Login then treats the request as anonymous.
    """
    if not user_id.isdigit():
        return None
    return dbase.session.get(User, int(user_id))
