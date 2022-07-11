from pathlib import Path

import tomli


def config_path():
    home_config = Path("~/.nua_cli.toml").expanduser()
    if home_config.exists():
        return home_config
    return Path(__file__).parent / "nua_cli_defaults.toml"


with open(config_path(), mode="rb") as rfile:
    config = tomli.load(rfile)
