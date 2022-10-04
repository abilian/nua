from pathlib import Path

import pytest

from .build_image import build_test_image

root = Path(__file__).parent

app_folder = [
    "flask_one_poetry",
    "flask_one_wheel",
    "flask_one_setup",
    "flask_pg_psyco_no_wheel",
    "flask_pg_psyco_wheel",
    "flask_sqla",
    "flask_sqla_sqlite_bind",
    "flask_sqla_sqlite_bind_wheel",
    "flask_two",
    "flask_upload_one",
    "flask_upload_bind_mount",
    "flask_upload_tmpfs",
    "flask_upload_sshfs",
]


@pytest.mark.parametrize("app", app_folder)
def test_build_all(app):
    build_test_image(root / app)
    print(Path.cwd())
