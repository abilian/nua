import tempfile
from pathlib import Path

from nua.lib import actions
from nua.lib.actions import python_package_installed


def test_actions_replace():  # noqa
    base_content = "some sample\nanother sample\n"
    pattern = "sample"
    replacement = "replaced"
    expected_content = "some replaced\nanother replaced\n"

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "sample.txt"
        path.write_text(base_content, encoding="utf8")
        file_pattern = str(Path(tmp_dir) / "*.txt")
        actions.replace_in(file_pattern, pattern, replacement)
        result = path.read_text(encoding="utf8")

        assert result == expected_content


def test_python_package_installed():
    assert python_package_installed("pip")
    assert not python_package_installed("uqwoiuei")


def test_actions_pyproject_true():
    folder = Path(__file__).parent.parent

    assert actions.is_python_project(folder)


def test_actions_pyproject_false():
    folder = Path(__file__).parent

    assert not actions.is_python_project(folder)


def test_check_python_version():
    assert actions.check_python_version()
