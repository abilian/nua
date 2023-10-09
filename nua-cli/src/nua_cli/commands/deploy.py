import json
import tempfile
from pathlib import Path

from cleez import Command
from cleez.command import Argument

from ..client import get_client
from .common import NUA_ENV, get_config, get_nua_host, sh, ssh

client = get_client()


# Hardcoded for now
class DeployCommand(Command):
    """Deploy app."""

    name = "deploy"

    arguments = [
        Argument("domain", help="Domain to deploy to."),
    ]

    def run(self, domain=None):
        """Deploy all apps."""
        config = get_config()
        host = get_nua_host()

        app_id = config["metadata"]["id"]
        deploy_config = {
            "site": [
                {
                    "image": app_id,
                    "domain": domain,
                }
            ],
        }

        temp_dir = tempfile.mkdtemp(prefix=f"nua-deploy-{app_id}-", dir="/tmp")  # noqa
        config_file = Path(temp_dir) / "deploy.json"
        Path(config_file).write_text(json.dumps(deploy_config, indent=2))

        sh(f"rsync -az --mkpath {config_file} root@{host}:{config_file}")
        ssh(f"{NUA_ENV}/bin/nua-orchestrator deploy {config_file}", host)
