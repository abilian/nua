import os

from flask_app.init_db import init_db


def register_cli(app):

    @app.cli.command("init-db")
    def _init_db():
        init_db(app)

    @app.cli.command("dump-config")
    def _dump_config():
        dump_config(app)


def dump_config(app):
    print("Environment:")
    for k, v in sorted(os.environ.items()):
        print(f"{k}: {v}")

    print()

    print("Config:")
    for k, v in sorted(app.config.items()):
        print(f"{k}: {v}")

    print()
