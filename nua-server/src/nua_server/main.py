"""Minimal Starlite application."""

from pathlib import Path

from starlite import Starlite, StaticFilesConfig, TemplateConfig
from starlite.contrib.jinja import JinjaTemplateEngine

from nua_server.pages import admin, home

handlers = home.get_handlers() + admin.get_handlers()

template_config = TemplateConfig(
    directory=Path(__file__).parent / "templates", engine=JinjaTemplateEngine
)

static_files_config = [
    StaticFilesConfig(directories=[Path(__file__).parent / "static"], path="/static"),
]


def create_app():
    return Starlite(
        route_handlers=handlers,
        template_config=template_config,
        static_files_config=static_files_config,
    )
