from pathlib import Path

import toml
from cleez.colors import bold

from ..helpers import ssh
from .base import Stage


class DeployStage(Stage):
    name = "deploy"

    def run(self):
        print(bold("Deploying apps..."))
        self.deploy_apps()

    def deploy_apps(self):
        for i, app_dir in enumerate(Path("apps").iterdir()):
            config_file = app_dir / "nua-config.toml"
            if not config_file.exists():
                config_file = app_dir / "nua" / "nua-config.toml"
            app_id = toml.load(config_file)["metadata"]["id"]
            domain = f"test{i}.tests.nua.rocks"
            ssh(f"python3 /vagrant/deploy-app.py {app_id} {domain}", user="nua")
