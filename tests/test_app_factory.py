from app.config import DevelopmentConfig, ProductionConfig, TestingConfig


def test_create_app_defaults_to_development(monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    from app import create_app

    app = create_app()
    assert app.config["DEBUG"] is DevelopmentConfig.DEBUG


def test_testing_config_uses_in_memory_db(app):
    assert app.config["TESTING"] is True
    assert (
        app.config["SQLALCHEMY_DATABASE_URI"] == TestingConfig.SQLALCHEMY_DATABASE_URI
    )


def test_production_config_disables_debug():
    from app import create_app

    app = create_app("production")
    assert app.config["DEBUG"] is ProductionConfig.DEBUG


def test_instance_folder_is_created(app):
    import os

    assert os.path.isdir(app.instance_path)
