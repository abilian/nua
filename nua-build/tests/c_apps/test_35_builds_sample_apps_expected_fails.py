import os
from pathlib import Path

import pytest
from nua.lib.nua_config import NuaConfig
from nua.lib.panic import Abort

from .build_image import build_test_image

root_dir = Path(__file__).parent / "data" / "sample-apps-expected-fail"
app_dirs = [dir.name for dir in root_dir.iterdir() if dir.is_dir()]


@pytest.mark.parametrize("dir_name", app_dirs)
def test_build_app(dir_name: str):
    orig_path = os.getcwd()
    dir = root_dir / dir_name
    with pytest.raises(Abort):
        build_test_image(dir)
    assert os.getcwd() == orig_path


def test_missing_license_is_proprietary_license():
    config_path = Path(__file__).parent / "data" / "config_missing_licence"
    config = NuaConfig(config_path)  # noqa F841
    expected = "Proprietary"
    result = config.build["license"]
    assert result == expected
