from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .. import config

# later maybe add for other than sqlite things like:
# pool_size= ...
# pool_recycle= ...

engine = create_engine(
    config.db.url,
    echo=config.db.echo,
)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
