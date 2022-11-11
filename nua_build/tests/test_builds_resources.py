from pathlib import Path

import pytest

from .build_image import build_test_image

root = Path(__file__).parent

app_folder = ["flask_pg_dock_psyco_wheel", "flask_mariadb_docker_wheel"]


# @pytest.mark.skip
@pytest.mark.parametrize("app", app_folder)
def test_build_all(app):
    build_test_image(root / "apps" / app)
    print(Path.cwd())
