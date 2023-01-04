import io
import runpy
from contextlib import redirect_stdout, suppress


def test_default_start():  # noqa
    f = io.StringIO()
    with redirect_stdout(f), suppress(ValueError):
        # Value Error if user Nua not created in buid environment (which is ok) :
        runpy.run_module("nua.build.defaults.start.py")
    output = f.getvalue()
    assert "This start.py file only" in output
