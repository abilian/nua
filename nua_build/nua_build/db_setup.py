"""Nua DB: search, create, upgrade.

Environment variables:
    NUA_DB_URL:
        url od the DB
    NUA_DB_LOCAL_DIR:
        if DB is local, directory to make if not exists. Option useful
        for SQLite.
"""
import os
from pathlib import Path

import toml
from addict import Dict

from . import __version__, config
from .db import requests
from .db.create import create_base
from .db.session import configure_session
from .rich_console import print_green, print_red


def setup_db():
    find_db_url()
    create_base()
    configure_session()
    setup_first_launch()


def default_config() -> dict:
    path = Path(__file__).parent.resolve() / "nua_defaults_settings.toml"
    settings = toml.load(path)
    return settings


def set_default_settings():
    global config  # required if changing config content

    current_db_url = config.nua.db.url
    current_db_local_dir = config.nua.db.local_dir
    config.nua = Dict(default_config())
    config.nua.db.url = current_db_url
    config.nua.db.local_dir = current_db_local_dir
    config.nua.instance = ""
    config.nua.version = __version__
    # store to DB
    requests.set_nua_settings(config.nua.to_dict())


def set_db_url_in_settings(settings):
    global config  # required if changing config content

    current_db_url = config.nua.db.url
    current_db_local_dir = config.nua.db.local_dir
    existing_nua_config = Dict(settings)
    existing_nua_config.db.url = current_db_url
    existing_nua_config.db.local_dir = current_db_local_dir
    # update live config
    config.nua = existing_nua_config
    # store to DB checked/updated/completed config
    requests.set_nua_settings(config.nua.to_dict())


def setup_first_launch():
    settings = requests.installed_nua_settings()
    if not settings:
        print_green(f"First launch: set Nua defaults in '{config.nua.db.url}'")
        return set_default_settings()
    installed_version = settings.get("version", "")
    if installed_version == __version__:
        return set_db_url_in_settings(settings)
    else:
        print_red(
            f"Replacing Nua settings from version {settings['version']} "
            f"by version {__version__} defaults"
        )
        return set_default_settings()


def _url_from_local_config():
    url, local_dir = (None, None)
    # local config in ~/nua_config.toml
    path = Path.home() / "nua_config.toml"
    if path.is_file():
        try:
            home_config = Dict(toml.load(path))
        except Exception:
            home_config = None
        if home_config:
            url = home_config.db.url
            local_dir = home_config.db.local_dir
    return url, local_dir


def _url_from_defaults():
    url, local_dir = (None, None)
    # default config in sources:
    source_config = Dict(default_config())
    url = source_config.db.url
    local_dir = source_config.db.local_dir
    return url, local_dir


def find_db_url() -> None:
    global config  # required if changing config content
    # environment:
    url = os.environ.get("NUA_DB_URL", "")
    local_dir = os.environ.get("NUA_DB_LOCAL_DIR", "")
    if not url:
        url, local_dir = _url_from_local_config()
    if not url:
        url, local_dir = _url_from_defaults()
    # store url in global config local_dir and url
    config.nua.db.local_dir = local_dir or ""
    if local_dir:
        Path(local_dir).mkdir(mode=0o755, parents=True, exist_ok=True)
    config.nua.db.url = url
    # print(f"find_db_url(): {config.nua.db.url=}")
