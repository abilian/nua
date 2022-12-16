from pathlib import Path

from nua.lib import actions


def test_actions_pyproject_true():  # noqa
    folder = Path(__file__).parent.parent

    assert actions.is_python_project(folder) == True


def test_actions_pyproject_false():  # noqa
    folder = Path(__file__).parent

    assert actions.is_python_project(folder) == False
