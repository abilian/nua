import logging
import shutil
from pathlib import Path

import toml

from nua.utils import panic, rm_rf, sh

logging.basicConfig(level=logging.INFO)


class BuildCmd:
    def __init__(self):
        if not Path("nua-config.toml").exists():
            panic("Can't find a nua-config.toml file")

        self.config = toml.load(open("nua-config.toml"))

    def run(self):
        self.setup_build_directory()
        self.build_with_docker()

    def setup_build_directory(self):
        rm_rf("_build")

        scripts_path = Path(__file__).parent.parent / "scripts"
        shutil.copytree(scripts_path, "_build")

        shutil.copy("nua-config.toml", "_build")

    def build_with_docker(self):
        sh("cd _build && docker build -t nua .")
