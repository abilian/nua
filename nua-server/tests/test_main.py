import pytest
from starlite.testing import TestClient

from nua_server.main import create_app


@pytest.fixture()
def app():
    return create_app()


def test_app(app) -> None:
    with TestClient(app=app) as client:
        assert "Nua" in client.get("/").text
