"""Script main entry point for Nua local: nua config export/update."""
import json
from pathlib import Path

import typer

from .. import config
from ..db.store import installed_nua_settings, set_nua_settings
from ..init import initialization
from ..util.deep_update import deep_update
from ..utils import parse_any_format

ALLOW_SUFFIX = {".json", ".toml", ".yaml", ".yml"}

app = typer.Typer()
arg_config = typer.Argument(None, metavar="config", help="Path config file.")


@app.command("export")
def export_nua_config(
    config_file: str = arg_config,
):
    """Export current Nua orchestrator config (JSON) to file or stdout."""
    initialization()
    content = installed_nua_settings()
    config_text = json.dumps(content, ensure_ascii=False, indent=4, sort_keys=True)
    if config_file:
        Path(config_file).write_text(config_text, encoding="utf8")
    else:
        print(config_text)


@app.command("update")
def update_nua_config(
    config_file: str = arg_config,
):
    """Update Nua orchestrator config from JSON or TOML file."""
    initialization()
    content = parse_any_format(Path(config_file))
    config_update(content)


@app.callback()
def main():
    """Manage the orchestrator config."""


def config_update(updates: dict):
    content = installed_nua_settings()
    deep_update(content, updates)
    config.set("nua", content)
    set_nua_settings(config.read("nua"))
