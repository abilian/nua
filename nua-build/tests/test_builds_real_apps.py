from pathlib import Path

import pytest

from .build_image import build_test_image
from .common import get_apps_root_dir

app_dirs = [
    "hedgedoc",
]


@pytest.mark.parametrize("dir_name", app_dirs)
def test_build_app(dir_name: str):
    path = get_apps_root_dir("real-apps") / dir_name
    build_test_image(path)
