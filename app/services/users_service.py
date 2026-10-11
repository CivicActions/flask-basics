from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.extensions import dbase
from app.models.users import User

UPDATABLE_FIELDS = {"name", "email", "is_active"}


class UserNotFound(Exception):
    pass


class EmailAlreadyExists(Exception):
    pass


def get_user(user_id: int) -> User:
    user = dbase.session.get(User, user_id)
    if user is None:
        raise UserNotFound(user_id)
    return user


def get_user_by_email(email: str) -> User | None:
    return dbase.session.scalar(
        dbase.select(User).where(User.email == email.strip().lower())
    )


def list_users(page: int = 1, per_page: int = 20):
    return dbase.paginate(
        dbase.select(User).order_by(User.id),
        page=page,
        per_page=per_page,
        max_per_page=100,
    )


def create_user(email: str, name: str) -> User:
    user = User(email=email.strip().lower(), name=name.strip())
    dbase.session.add(user)
    _commit_or_raise_duplicate(email)
    return user


def update_user(user_id: int, **fields) -> User:
    user = get_user(user_id)
    for key, value in fields.items():
        if key not in UPDATABLE_FIELDS:
            continue  # ignore anything not whitelisted (id, password_hash, ...)
        if key == "email":
            value = value.strip().lower()
        setattr(user, key, value)
    _commit_or_raise_duplicate(fields.get("email", user.email))
    return user


def delete_user(user_id: int) -> None:
    user = get_user(user_id)
    dbase.session.delete(user)
    dbase.session.commit()


def _commit_or_raise_duplicate(email: str) -> None:
    try:
        dbase.session.commit()
    except IntegrityError:
        dbase.session.rollback()
        raise EmailAlreadyExists(email)


def upsert_from_google(userinfo: dict) -> User:
    """Create or update a user from Google's OpenID Connect userinfo claims."""
    user = dbase.session.scalar(
        dbase.select(User).where(User.google_sub == userinfo["sub"])
    )
    if user is None:
        user = User(google_sub=userinfo["sub"])
        dbase.session.add(user)

    user.email = userinfo["email"].strip().lower()
    user.email_verified = userinfo.get("email_verified", False)
    user.name = userinfo.get("name")
    user.picture = userinfo.get("picture")
    user.last_login_at = datetime.now(timezone.utc)

    dbase.session.commit()
    return user
