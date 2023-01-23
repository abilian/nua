import pytest

from nua.orchestrator.utils import base20

INT_B20 = (
    (0, "b"),
    (1, "c"),
    (19, "z"),
    (20, "cb"),
    (21, "cc"),
    (400, "cbb"),
    (8000, "cbbb"),
)


@pytest.mark.parametrize("param", INT_B20)
def test_display_base20(param):
    input = param[0]
    expected = param[1]

    result = base20(input)

    assert result == expected
