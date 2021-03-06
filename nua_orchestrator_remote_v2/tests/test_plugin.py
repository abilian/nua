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
import sys

import pytest

try:
    import nua_plugin_test
except ImportError:
    print("For this test, install required module: nua_plugin_test")

from time import sleep

import zmq
from tinyrpc import RPCClient
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.zmq import ZmqClientTransport
from typer.testing import CliRunner

from nua_orchestrator import config
from nua_orchestrator.main import app

from .utils import force_start, force_stop

zmq_ctx = zmq.Context()


def get_proxy():
    address = config.read("nua", "zmq", "address")
    port = config.read("nua", "zmq", "port")
    rpc_client = RPCClient(
        JSONRPCProtocol(),
        ZmqClientTransport.create(zmq_ctx, f"tcp://{address}:{port}", timeout=2.0),
    )
    proxy = rpc_client.get_proxy()
    return proxy


@pytest.mark.skipif(
    "nua_plugin_test" not in sys.modules, reason="requires the nua_plugin_test"
)
def test_plugins_loaded():
    plugin1 = "plugin_multiply"
    plugin2 = "plugin_substract"
    runner = CliRunner()
    runner.invoke(app, "restart")
    result = runner.invoke(app, "status")

    assert result.exit_code == 0
    assert plugin1 in result.stdout
    assert plugin2 in result.stdout


@pytest.mark.skipif(
    "nua_plugin_test" not in sys.modules, reason="requires the nua_plugin_test"
)
def test_plugin_multiply():
    runner = CliRunner()
    runner.invoke(app, "start")
    proxy = get_proxy()

    result = proxy.plugin_multiply(11, 5)

    assert result == 55


@pytest.mark.skipif(
    "nua_plugin_test" not in sys.modules, reason="requires the nua_plugin_test"
)
def test_plugin_substract():
    runner = CliRunner()
    runner.invoke(app, "start")
    proxy = get_proxy()

    result = proxy.plugin_substract(100, 20)

    assert result == 80
