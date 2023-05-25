from pathlib import Path

from nua.agent.auto_install import detector_classes, register_detectors
from nua.agent.detectors.base_detector import BaseDetector
from nua.agent.detectors.python_source import PythonSource
from nua.agent.detectors.python_wheels import PythonWheels
from nua.lib.backports import chdir


def test_register_detectors_loading():
    register_detectors()
    assert len(detector_classes) > 0


def test_register_detectors_loaded_content():
    register_detectors()
    assert all(issubclass(detector, BaseDetector) for detector in detector_classes)


def test_register_detectors_loaded_python():
    register_detectors()
    assert PythonSource in detector_classes


def test_register_detectors_loaded_python_wheels():
    register_detectors()
    assert PythonWheels in detector_classes


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
