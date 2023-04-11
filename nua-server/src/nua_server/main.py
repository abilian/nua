"""Main Sanic application."""

import snoop

# Imported for side-effects => don't remove the assert statements
from nua_server.pages import admin, home

from .app import app

assert admin
assert home
assert app


snoop.install()

# Old Starlite config

# handlers = home.get_handlers() + admin.get_handlers()
#
#
# template_config = TemplateConfig(
#     directory=Path(__file__).parent / "templates", engine=JinjaTemplateEngine
# )
#
# static_files_config = [
#     StaticFilesConfig(directories=[Path(__file__).parent / "static"], path="/static"),
# ]

# app = Starlite(
#     route_handlers=handlers,
#     template_config=template_config,
#     static_files_config=static_files_config,
# )
