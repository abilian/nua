from pathlib import Path

from nua.lib.backports import chdir

from nua.agent.detectors import PythonSource, PythonWheels


def test_pyproject_true():
    folder = Path(__file__).parent.parent
    with chdir(folder):
        assert PythonSource.detect()


def test_pyproject_false():
    folder = Path(__file__).parent
    with chdir(folder):
        assert not PythonSource.detect()


def test_pythonwheels_false():
    folder = Path(__file__).parent
    with chdir(folder):
        assert not PythonWheels.detect()
