import os

import pytest

from .build_image import build_test_image
from .common import get_apps_root_dir

root_dir = get_apps_root_dir("sample-apps")
app_dirs = [dir.name for dir in root_dir.iterdir() if dir.is_dir()]


@pytest.mark.parametrize("dir_name", app_dirs)
def test_build_app(dir_name: str):
    orig_path = os.getcwd()
    dir = root_dir / dir_name
    build_test_image(dir)
    assert os.getcwd() == orig_path
