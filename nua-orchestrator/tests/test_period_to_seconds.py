import pytest

from nua.orchestrator.utils import period_to_seconds

STR_INT = (
    (None, 0),
    ("", 0),
    ("0", 0),
    ("4", 4),
    ("10000", 10000),
    ("5 s", 5),
    ("2 h", 7200),
    ("10min", 600),
    ("3d", 259200),
)


@pytest.mark.parametrize("param", STR_INT)
def test_size_to_bytes(param):
    input = param[0]
    expected = param[1]
    assert period_to_seconds(input) == expected
