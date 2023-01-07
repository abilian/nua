from sqlalchemy import TIMESTAMP, Column, Integer, String, text
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class Host(Base, SerializerMixin):
    """contains the Nua host information.

    Note: Could be also stored in the Na app blob. Thus, not clear if that
    table will be used.
    """

    __tablename__ = "host"

    id = Column(Integer, primary_key=True, unique=True)
    hostname = Column(String(254), unique=True)
    display_name = Column(String(512), server_default=text("''"))
    email = Column(String(512), server_default=text("''"))
    private_key = Column(String(4096), server_default=text("''"))
    ts = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    creation_time = Column(
        TIMESTAMP, nullable=False, index=True, server_default=text("CURRENT_TIMESTAMP")
    )
