from datetime import datetime

from sqlalchemy import TIMESTAMP, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class Host(Base, SerializerMixin):
    """contains the Nua host information.

    Note: Could be also stored in the Na app blob. Thus, not clear if that
    table will be used.
    """

    __tablename__ = "host"

    # TODO: sensible contraints / defaults
    # XXX: are the fields length below justified?
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    hostname: Mapped[str] = mapped_column(String(254), unique=True)
    display_name: Mapped[str] = mapped_column(String(512), default="")
    email: Mapped[str] = mapped_column(String(512), default="")
    private_key: Mapped[str] = mapped_column(String(4096), default="")

    # XXX: what is the difference between ts and creation_time?
    # XXX: why do we need an index on creation_time?
    ts: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)
    creation_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, index=True, server_default=text("CURRENT_TIMESTAMP")
    )

    # Was:
    # id = Column(Integer, primary_key=True, unique=True)
    # hostname = Column(String(254), unique=True)
    # display_name = Column(String(512), server_default=text("''"))
    # email = Column(String(512), server_default=text("''"))
    # private_key = Column(String(4096), server_default=text("''"))
    #
    # ts = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    # creation_time = Column(
    #     TIMESTAMP, nullable=False, index=True, server_default=text("CURRENT_TIMESTAMP")
    # )
