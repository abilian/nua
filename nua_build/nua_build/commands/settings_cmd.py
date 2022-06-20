"""Sttings management."""
import json
from pathlib import Path
from typing import Optional

import toml
import typer

from ..db import requests

app = typer.Typer()

argument_show_app_id = typer.Argument(
    None, metavar="app", help="Id of the app, 'nua' for nua-build settings."
)
argument_load_app_id = typer.Argument(
    None, metavar="app", help="Id of the app, 'nua' for nua-build settings."
)
argument_load_config = typer.Argument(
    None, metavar="config", help="Path to the package dir or 'nua-config.toml' file."
)
option_show_all = typer.Option(
    False,
    "--all",
    "-a",
    metavar="all",
    help="Dump all settings as JSON list.",
)
option_show_json = typer.Option(
    False,
    "--json",
    metavar="json",
    help="Use JSON format for the output.",
)
option_show_toml = typer.Option(
    False,
    "--toml",
    metavar="toml",
    help="Use TOML format for the output.",
)


def print_formatted(content, format):
    if format == "json":
        print(
            json.dumps(
                content,
                sort_keys=True,
                indent=4,
                ensure_ascii=False,
            )
        )
    else:  # toml
        print(toml.dumps(content))


def dump_all_settings() -> None:
    """Dump all settings from DB (.json)."""
    settings = requests.dump_all_settings()
    print_formatted(settings, "json")


def dump_nua_settings(format) -> None:
    """Dump Nua settings from DB (.toml or .json)."""
    settings = requests.installed_nua_settings()
    print_formatted(settings, "toml")


def dump_app_id_settings(format) -> None:
    """Dump app settings from DB (.toml or .json)."""
    print("Not implemented")


def _select_output_format(json_flag: bool, toml_flag: bool) -> str:
    output_format = "toml"
    if json_flag:
        output_format = "json"
    if toml_flag:
        output_format = "toml"
    return output_format


@app.command()
def show(
    app_id: Optional[str] = argument_show_app_id,
    all_flag: bool = option_show_all,
    json_flag: bool = option_show_json,
    toml_flag: bool = option_show_toml,
) -> None:
    """Display settings of an app or of Nua by default."""
    if all_flag:
        return dump_all_settings()
    output_format = _select_output_format(json_flag, toml_flag)
    if not app_id or app_id in {"nua", "nuad", "nua-build"}:
        return dump_nua_settings(output_format)
    return dump_app_id_settings(output_format)


@app.command()
def load(
    app_id: str = argument_load_app_id,
    config_file: str = argument_load_config,
) -> None:
    """Load settings from .toml or .json file for Nua or some app."""
    if not config_file:
        raise ValueError(f"Config path argument is required.")
    path = Path(config_file)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: '{config_file}'")
    if path.suffic.lower() == ".toml":
        content = toml.load(path)
    else:  # expect some json
        with open(config_file, encoding="utf8") as file:
            content = json.load(file)
    if app_id in {"nua", "nuad", "nua-build"}:
        requests.set_nua_settings(content)
    else:
        print("Not implemented.")
