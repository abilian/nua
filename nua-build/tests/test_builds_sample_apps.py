from pathlib import Path

import pytest

from .build_image import build_test_image
from .common import get_apps_root_dir

root_dir = get_apps_root_dir("sample-apps")
app_dirs = [dir for dir in root_dir.iterdir() if dir.is_dir()]


@pytest.mark.parametrize("dir", app_dirs)
def test_build_app(dir: Path):
    build_test_image(dir)
