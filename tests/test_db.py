from sqlalchemy import Integer, String, inspect
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base


class Widget(Base):
    """Ad-hoc model defined once at module scope, purely to exercise the
    SQLAlchemy wiring. `db.metadata`/`Base` are shared singletons (not
    per-app), so defining this class more than once (e.g. inside a test
    function) would register duplicate tables that leak into every
    `create_app()` call for the rest of the test session. `Base` is the
    same declarative base as `dbase.Model` (see app/extensions.py) but,
    unlike it, is statically typed so mypy can check it as a base class.
    """

    __tablename__ = "widgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


def test_db_can_create_query_and_commit(app, db):
    db.session.add(Widget(name="sprocket"))
    db.session.commit()

    widget = db.session.query(Widget).filter_by(name="sprocket").first()
    assert widget is not None
    assert widget.name == "sprocket"


def test_db_data_isolated_between_app_instances(app, db):
    # A fresh `app` fixture means a fresh create_app("testing") -> a new,
    # separate in-memory sqlite engine. The "widgets" table exists here too
    # (schema is shared via db.metadata), but no *rows* should carry over
    # from the previous test, since each app has its own physical db.
    assert "widgets" in inspect(db.engine).get_table_names()
    assert db.session.query(Widget).count() == 0
