from nua_server.main import app
from starlite.testing import TestClient


def test_app() -> None:
    with TestClient(app=app) as client:
        assert "Nua" in client.get("/").text
