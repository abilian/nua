from pathlib import Path

import pytest

from .build_image import build_test_image

root = Path(__file__).parent

app_folder = [
    "flask_one",
    "flask_pg_psyco",
    "flask_sqla",
    "flask_sqla_sqlite_bind",
    "flask_two",
    "flask_upload_one",
    "flask_upload_sshfs",
]


@pytest.mark.parametrize("app", app_folder)
def test_build_all(app):
    build_test_image(root / app)
