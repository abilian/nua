from starlite.testing import TestClient

from nua_server.main import app


def test_app() -> None:
    with TestClient(app=app) as client:
        assert "Nua" in client.get("/").text
