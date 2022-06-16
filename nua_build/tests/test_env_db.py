import os
from pathlib import Path

from typer.testing import CliRunner

from nua_build.main import app

runner = CliRunner()

import pytest

test_db_path = "/var/tmp/pytest_nua_test"
test_db_name = "test.db"
test_db_url = f"sqlite:///{test_db_path}/{test_db_name}"


@pytest.fixture()
def environment():
    prior_db_url = os.environ.get("NUA_DB_URL")
    os.environ["NUA_DB_URL"] = test_db_url
    prior_db_path = os.environ.get("NUA_DB_LOCAL_DIR")
    os.environ["NUA_DB_LOCAL_DIR"] = test_db_path
    db_file = Path(test_db_path) / test_db_name
    if db_file.is_file():
        db_file.unlink()
    if Path(test_db_path).is_dir():
        Path(test_db_path).rmdir()
    runner = CliRunner()

    yield runner

    if prior_db_url is None:
        del os.environ["NUA_DB_URL"]
    else:
        os.environ["NUA_DB_URL"] = prior_db_url
    if prior_db_path is None:
        del os.environ["NUA_DB_LOCAL_DIR"]
    else:
        os.environ["NUA_DB_LOCAL_DIR"] = prior_db_path

    if db_file.is_file():
        db_file.unlink()
    if Path(test_db_path).is_dir():
        Path(test_db_path).rmdir()


class TestEnv:
    def test_env(self, environment):
        db_file = Path(test_db_path) / test_db_name

        assert not Path(test_db_path).exists()

        result = runner.invoke(app)

        assert result.exit_code == 0
        assert Path(test_db_path).is_dir()
        assert Path(db_file).is_file()
