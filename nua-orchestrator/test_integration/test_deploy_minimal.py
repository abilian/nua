import json
from pathlib import Path

from .deployer import deploy_one_site
from .initialization import ensure_docker_image

ALLOW = {".json", ".toml", ".yaml", ".yml"}
TARGET_DIR = Path(__file__).parent / "configs_minimal"


def test_configs_minimal():
    test_path = Path(__file__).parent / "configs_minimal"
    deploy_file = test_path / "deploy.json"
    ensure_docker_image(test_path)
    deploy_one_site(deploy_file)
