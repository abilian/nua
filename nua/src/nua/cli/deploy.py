import shutil
from pathlib import Path

from nua.utils import rm_rf, sh


class DeployCmd:
    def __init__(self, config):
        self.config = config

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
