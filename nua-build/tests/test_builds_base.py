from pathlib import Path

import pytest

from .build_image import build_test_image

root = Path(__file__).parent

app_dirs = [
    "echo_two_ports",
    "flask_one_poetry",
    "flask_one_setup",
    "flask_one_wheel",
    "flask_pg_psyco_no_wheel",
    "flask_pg_psyco_wheel",
    "flask_sqla_sqlite_bind_wheel",
    "flask_sqla_sqlite_bind",
    "flask_sqla",
    "flask_two",
    "flask_upload_bind_mount",
    "flask_upload_one",
    "flask_upload_sshfs",
    "flask_upload_tmpfs",
]

# app_dirs = [dir for dir in (root / "apps").iterdir() if dir.is_dir()]


@pytest.mark.parametrize("dir_name", app_dirs)
def test_build_all(dir_name: str):
    path = root / "apps" / dir_name
    build_test_image(path)
