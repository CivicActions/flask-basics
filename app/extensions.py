from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Typed declarative base.

    flask-sqlalchemy's ``db.Model`` is assigned dynamically at runtime
    (``self.Model = ...`` inside ``SQLAlchemy.__init__``), so mypy cannot
    resolve it as a base class when subclassed elsewhere (e.g.
    `class BaseModel(dbase.Model)`). Passing an explicit, statically typed
    `DeclarativeBase` subclass as `model_class` keeps `db.Model` and `Base`
    equivalent at runtime while giving mypy a real class to type-check
    against — models should import and subclass `Base` directly instead of
    `dbase.Model`.
    """


# Instantiated without an app so they can be bound later via init_app(),
# which avoids circular imports between extensions and blueprints.
# NOTE: init order matters at bind time — SQLAlchemy must be init_app()'d
# before Marshmallow (see create_app()) so flask-marshmallow's optional
# SQLAlchemy integration (SQLAlchemyAutoSchema) can find the db extension.
dbase = SQLAlchemy(model_class=Base)
marsh = Marshmallow()
migrate = Migrate()
