"""Nua DB: search, create, upgrade

Environment variables:
    NUA_DB_URL:
        url od the DB
    NUA_DB_LOCAL_DIR:
        if DB is local, directory to make if not exists. Option useful
        for SQLite.
"""
import json
import os
from pathlib import Path
from typing import Optional

import toml
from addict import Dict

from . import __version__, config
from .db import requests
from .db.create import create_base
from .db.session import configure_session
from .rich_console import print_green


def setup_db():
    find_db_url()
    create_base()
    configure_session()
    setup_first_launch()


def default_config() -> dict:
    path = Path(__file__).parent.resolve() / "nua_defaults.toml"
    return toml.load(path)


def upgrade_settings(settings):
    print_green(
        f"Upgrading Nua settings version from {settings['version']} "
        f"to {__version__}"
    )
    settings["version"] = __version__


def setup_first_launch():
    global config  # required if changing config content

    current_db_url = config.nua.db.url
    current_db_local_dir = config.nua.db.local_dir
    # print("Debug: DB is:", config.db.url)
    settings = requests.installed_nua_settings()
    if settings:
        installed_version = settings.get("version", "")
        if installed_version != __version__:
            # FIXME : check if version is actually >
            upgrade_settings(settings)
        existing_nua_config = Dict(settings)
        existing_nua_config.db.url = current_db_url
        existing_nua_config.db.local_dir = current_db_local_dir
        # update live config
        config.nua = existing_nua_config
        # store to DB checked/updated/completed config
        requests.set_nua_settings(config.nua.to_dict())
    else:
        print_green("Nua first launch")
        print_green(f"    - loading defaults in '{config.db.url}'")
        config = Dict(default_config())
        config.nua.db.url = current_db_url
        config.nua.db.local_dir = current_db_local_dir
        config.nua.instance = ""
        config.nua.version = __version__
        # store to DB
        requests.set_nua_settings(config.nua.to_dict())
    print(requests.dump_settings())


def find_db_url() -> None:
    global config  # required if changing config content
    # environment:
    url = os.environ.get("NUA_DB_URL", "")
    local_dir = os.environ.get("NUA_DB_LOCAL_DIR", "")
    if not url:
        # local config in /nua
        path = Path("/nua/data/nua_config.toml")
        if path.is_file():
            try:
                config = Dict(toml.load(path))
            except Exception:
                config = None
            if config:
                url = config.db.url
                local_dir = config.db.local_dir
    if not url:
        # use local /var/tmp (for development)
        local_dir = "/var/tmp/nua"
        url = f"sqlite:///{local_dir}/nua_build.db"
    # store url in global config local_dir and url
    config.nua.db.local_dir = local_dir or ""
    if local_dir:
        Path(local_dir).mkdir(mode=0o755, parents=True, exist_ok=True)
    config.nua.db.url = url
