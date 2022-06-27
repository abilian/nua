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

from . import __version__, config
from .db import store
from .db.create import create_base
from .db.session import configure_session
from .deep_access_dict import DeepAccessDict
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

    current_db_url = config.read("nua", "db", "url")
    current_db_local_dir = config.read("nua", "db", "local_dir")
    config.set("nua", default_config())
    config.set("nua", "db", "url", current_db_url)
    config.set("nua", "db", "local_dir", current_db_local_dir)
    config.set("nua", "instance", "")
    config.set("nua", "version", __version__)
    # store to DB
    store.set_nua_settings(config.read("nua"))


def set_db_url_in_settings(settings):
    global config  # required if changing config content

    current_db_url = config.read("nua", "db", "url")
    current_db_local_dir = config.read("nua", "db", "local_dir")
    existing_nua_config = DeepAccessDict(settings)
    existing_nua_config.set("db", "url", current_db_url)
    existing_nua_config.set("db", "local_dir", current_db_local_dir)
    # update live config
    config.set("nua", existing_nua_config)
    # store to DB checked/updated/completed config
    store.set_nua_settings(config.read("nua"))


def setup_first_launch():
    settings = store.installed_nua_settings()
    if not settings:
        print_green(
            f"First launch: set Nua defaults in '{config.read('nua','db','url')}'"
        )
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
            home_config = DeepAccessDict(toml.load(path))
        except Exception:
            home_config = None
        if home_config:
            url = home_config.read("db", "url")
            local_dir = home_config.read("db", "local_dir")
    return url, local_dir


def _url_from_defaults():
    url, local_dir = (None, None)
    # default config in sources:
    source_config = DeepAccessDict(default_config())
    url = source_config.read("db", "url")
    local_dir = source_config.read("db", "local_dir")
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
    config.set("nua", "db", "local_dir", local_dir or "")
    if local_dir:
        Path(local_dir).mkdir(mode=0o755, parents=True, exist_ok=True)
    config.set("nua", "db", "url", url)
    # print(f"find_db_url(): {config.nua.db.url=}")
