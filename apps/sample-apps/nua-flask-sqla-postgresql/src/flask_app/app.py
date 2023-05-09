from flask import Flask

from . import constants
from .extensions import db
from .init_db import init_db
from .views import register_views


def create_app():
    app = Flask(__name__)
    username = constants.DB_USERNAME
    password = constants.DB_PASSWORD
    host = constants.DB_HOST or "localhost"
    port = constants.DB_PORT or 5432
    name = constants.DB_NAME or "nua_test"
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"postgresql://{username}:{password}@{host}:{port}/{name}"
    # print(f"postgresql://{username}:{password}@{host}:{port}/{name}")
    db.init_app(app)

    register_views(app)

    # register_cli(app)
    init_db(app)

    return app
