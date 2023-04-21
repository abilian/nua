#!/usr/bin/env python3

import argparse
import json
import os
import tempfile
from pathlib import Path
from subprocess import run

NUA_ENV = "/home/nua/env"


def main(app_id: str, domain: str):
    deploy_config = {
        "site": [
            {
                "image": app_id,
                "domain": domain,
            }
        ],
    }

    temp_dir = tempfile.mkdtemp(prefix=f"nua-deploy-{app_id}-", dir="/tmp")
    config_file = Path(temp_dir) / "deploy.json"
    Path(config_file).write_text(json.dumps(deploy_config, indent=2))

    cmd = f"{NUA_ENV}/bin/nua-orchestrator deploy {config_file}"
    env = os.environ.copy()
    env["NUA_CERTBOT_STRATEGY"] = "none"
    run(cmd, shell=True, check=True, env=env)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbosity", action="count", help="Increase output verbosity"
    )
    parser.add_argument("app", help="Application ID")
    parser.add_argument("domain", help="Domain name")

    args = parser.parse_args()
    main(args.app, args.domain)
