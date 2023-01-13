import os
from pathlib import Path

import pytest

from .deployer import deploy_one_site

ALLOW = {".json", ".toml", ".yaml", ".yml"}
TARGET_DIR = Path(__file__).parent / "configs_a"
DEPLOY_FILES = [str(p) for p in sorted(TARGET_DIR.glob("*")) if p.suffix in ALLOW]


os.environ["NUA_CERTBOT_TEST"] = "1"
os.environ["NUA_CERTBOT_VERBOSE"] = "1"


@pytest.mark.parametrize("deploy_file", DEPLOY_FILES)  # noqa AAA01
def test_configs_a(deploy_file: str):
    deploy_one_site(deploy_file)
