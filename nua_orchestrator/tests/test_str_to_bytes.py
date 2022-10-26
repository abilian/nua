import pytest

from nua_orchestrator.utils import size_to_bytes

STR_INT = (
    (None, 0),
    ("", 0),
    ("0", 0),
    ("4", 4),
    ("10000", 10000),
    ("1 kb", 1024),
    ("2 K", 2048),
    ("2.5 K", 2560),
    ("10 Mb", 10485760),
    ("2.0 GB", 2147483648),
    ("1t", 1099511627776),
)


@pytest.mark.parametrize("param", STR_INT)
def test_none(param):
    input = param[0]
    expected = param[1]
    assert size_to_bytes(input) == expected
