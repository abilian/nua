from sqlalchemy import create_engine

from .. import config
from .model.base import Base


def create_base():
    # assert config.db.backend == "sqlite"

    engine = create_engine(
        config.read("nua", "db", "url"),
        # echo=config.nua.db.echo,
    )
    Base.metadata.create_all(engine)
