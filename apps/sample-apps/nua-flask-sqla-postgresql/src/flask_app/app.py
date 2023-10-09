import os

from flask import Flask

from . import constants
from .cli import register_cli
from .extensions import db
from .views import register_views


def create_app():
    app = Flask(__name__)
    app.config.from_prefixed_env()

    if "SQLALCHEMY_DATABASE_URI" not in app.config:
        username = constants.DB_USERNAME or ""
        password = constants.DB_PASSWORD or ""
        host = constants.DB_HOST or "localhost"
        port = constants.DB_PORT or 5432
        name = constants.DB_NAME or "nua_test"
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f"postgresql://{username}:{password}@{host}:{port}/{name}"

    db.init_app(app)
    register_views(app)
    register_cli(app)
    return app
