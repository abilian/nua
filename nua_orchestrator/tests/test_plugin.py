import sys

from typer.testing import CliRunner

from nua_orchestrator.main import app

from .utils import force_start, force_stop

try:
    import nua_plugin_test
except ModuleNotFoundError:
    print("Install required module: nua_plugin_test")
    sys.exit(1)


def test_plugins_loaded():
    """This test depends on:
    - module nua_plugin_test installed
    - config contains:
        [rpc]
          status_show_all = true
      and:
        [[rpc.plugin]]
          module = "nua_plugin_test.methods.test_plugin"
          class = "RPCPluginTest"
    """
    plugin1 = "plugin_multiply"
    plugin2 = "plugin_substract"
    runner = CliRunner()
    force_stop(runner)

    runner.invoke(app, "restart")
    result = runner.invoke(app, "status")

    assert result.exit_code == 0
    assert plugin1 in result.stdout
    assert plugin2 in result.stdout
