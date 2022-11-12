from pathlib import Path

import pytest

from .build_image import build_test_image

root = Path(__file__).parent

app_dirs = [
    "flask_pg_dock_psyco_wheel",
    "flask_mariadb_docker_wheel",
]


@pytest.mark.parametrize("dir_name", app_dirs)
def test_build_all(dir_name: str):
    path = root / "apps" / dir_name
    build_test_image(path)
