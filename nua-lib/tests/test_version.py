import pytest


def test_version_string():  # noqa
    from nua.lib import __version__

    version_split = __version__.split(".")

    assert len(version_split) >= 2