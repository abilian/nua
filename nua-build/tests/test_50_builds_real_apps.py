import os

import pytest

from .build_image import build_test_image
from .common import get_apps_root_dir

app_dirs = [
    "hedgedoc",
    "dolibarr",
]


@pytest.mark.parametrize("dir_name", app_dirs)
@pytest.mark.slow
def test_build_app(dir_name: str):
    path = get_apps_root_dir("real-apps") / dir_name
    orig_path = os.getcwd()
    build_test_image(path)
    assert os.getcwd() == orig_path
