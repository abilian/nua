import logging
from pathlib import Path

import fire
import toml

from nua.cli.build import BuildCmd
from nua.cli.deploy import DeployCmd
from nua.utils import console, panic

logging.basicConfig(level=logging.INFO)


class CLI:
    def build(self):
        console.print("Starting build")
        BuildCmd(get_config()).run()

    def deploy(self):
        console.print("Starting deploy")
        DeployCmd(get_config()).run()


def get_config():
    if not Path("nua-config.toml").exists():
        panic("Can't find a nua-config.toml file")

    return toml.load(open("nua-config.toml"))


def main():
    fire.Fire(CLI)
