"""List available images."""
import json
from typing import Optional

import toml
import typer

from ..db import requests

app = typer.Typer()

argument_config = typer.Argument(
    None, metavar="config", help="Path to the package dir or 'nua-config.toml' file."
)


@app.command("dump_all_settings")
def dump_all_settings_cmd() -> None:
    """Dump all settings from DB (.json)."""
    settings = requests.dump_all_settings()
    print(
        json.dumps(
            settings,
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )
    )


@app.command("dump_nua_settings")
def dump_nua_settings() -> None:
    """Dump Nua settings from DB (.toml)."""
    settings = requests.installed_nua_settings()
    print(toml.dumps(settings))


@app.command("load_nua_settings")
def load_nua_settings(config_file: Optional[str] = argument_config) -> None:
    """Load Nua settings from .toml file."""
    settings = toml.load(config_file)
    requests.set_nua_settings(settings)
