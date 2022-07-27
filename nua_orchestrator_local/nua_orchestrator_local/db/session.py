from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .. import config

# later maybe add for other than sqlite things like:
# pool_size= ...
# pool_recycle= ...

Session = scoped_session(sessionmaker())


def configure_session():
    # print("DB url in Session:", config.nua.db.url)
    Session.remove()
    engine = create_engine(
        config.read("nua", "db", "url"),
        # echo=config.nua.db.echo or False,
    )
    Session.configure(bind=engine)
