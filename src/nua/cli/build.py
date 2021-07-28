import shutil
from pathlib import Path

import toml

from nua.utils import panic, rm_rf, sh


class BuildCmd:
    def __init__(self, config):
        self.config = config
        if not Path("nua-config.toml").exists():
            panic("Can't find a nua-config.toml file")

        self.config = toml.load(open("nua-config.toml"))

    @property
    def app_id(self) -> str:
        return self.config["metadata"]["id"]

    @property
    def app_version(self) -> str:
        return self.config["metadata"]["version"]

    def run(self):
        self.setup_build_directory()
        self.build_with_docker()

    def setup_build_directory(self):
        rm_rf("_build")

        scripts_path = Path(__file__).parent.parent / "scripts"
        shutil.copytree(scripts_path, "_build")

        shutil.copy("nua-config.toml", "_build")

    def build_with_docker(self):
        sh(f"cd _build && docker build -t {self.app_id}:{self.app_version} .")
