import tempfile
from pathlib import Path

from nua.lib import actions


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
    assert actions.python_package_installed("pip")
    assert not actions.python_package_installed("uqwoiuei")


def test_check_python_version():
    assert actions.check_python_version()
