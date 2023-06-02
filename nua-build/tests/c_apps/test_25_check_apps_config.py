import pydantic
import pytest
from nua.lib.nua_config import NuaConfig, NuaConfigError

from .common import get_apps_root_dir

root_dir_sample = get_apps_root_dir("sample-apps")
root_dir_real = get_apps_root_dir("real-apps")
app_dirs_sample = [dir.name for dir in root_dir_sample.iterdir() if dir.is_dir()]
app_dirs_real = [dir.name for dir in root_dir_real.iterdir() if dir.is_dir()]


def check_nua_config(dir: str) -> bool:
    try:
        NuaConfig(dir)
    except pydantic.error_wrappers.ValidationError as valid_error:
        print(valid_error)
        print("Some error in nua config file.")
        return False
    except NuaConfigError as e:
        print(e)
        print("Some error in nua config file.")
        return False
    return True


@pytest.mark.parametrize("dir_name", app_dirs_sample)
def test_config_sample_app(dir_name: str):
    dir = root_dir_sample / dir_name
    result = check_nua_config(str(dir))
    assert result


@pytest.mark.parametrize("dir_name", app_dirs_real)
def test_config_real_app(dir_name: str):
    dir = root_dir_real / dir_name
    result = check_nua_config(str(dir))
    assert result
