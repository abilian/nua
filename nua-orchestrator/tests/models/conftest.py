import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nua.orchestrator.db.model.base import Base

DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def db_engine(request):
    """Yields a SQLAlchemy engine which is suppressed after the test session"""
    db_url = DB_URL
    engine = create_engine(db_url, echo=True)

    yield engine

    engine.dispose()


@pytest.fixture(scope="session")
def db_tables(db_engine):
    Base.metadata.create_all(db_engine)
    yield
    Base.metadata.drop_all(db_engine)


@pytest.fixture
def db_session(db_engine, db_tables):
    """Returns a sqlalchemy session, and after the test tears down everything properly."""
    connection = db_engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()
