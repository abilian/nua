from sqlalchemy import create_engine

from .model import auth
from .model.base import Base


def create_base(config):
    backend = config["db"]["backend"]
    url = config["db"]["url"]

    assert backend == "sqlite"

    engine = create_engine(url)
    Base.metadata.create_all(engine)
