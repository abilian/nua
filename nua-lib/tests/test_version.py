from nua.lib import __version__


def test_version_string():  # noqa
    version_split = __version__.split(".")

    assert len(version_split) >= 2
