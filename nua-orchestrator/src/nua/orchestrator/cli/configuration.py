"""Script main entry point for Nua local: nua config export/update."""
import json
import sys
from pathlib import Path

import typer

from .. import config
from ..db.store import installed_nua_settings, set_nua_settings
from ..util.deep_update import deep_update
from ..utils import parse_any_format
from .init import initialization

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
    if config_file:
        Path(config_file).write_text(
            json.dumps(
                content,
                ensure_ascii=False,
                indent=4,
                sort_keys=True,
            ),
            encoding="utf8",
        )
    else:
        json.dump(
            content,
            sys.stdout,
            ensure_ascii=False,
            indent=4,
            sort_keys=True,
        )


@app.command("update")
def update_nua_config(
    config_file: str = arg_config,
):
    """Update Nua orchestrator config from JSON or TOML file."""
    initialization()
    content = parse_any_format(Path(config_file))
    config_update(content)


def config_update(updates: dict):
    content = installed_nua_settings()
    deep_update(content, updates)
    config.set("nua", content)
    set_nua_settings(config.read("nua"))