from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Index, Table, text
from sqlalchemy.dialects.sqlite import (
    BLOB,
    BOOLEAN,
    CHAR,
    DATE,
    DATETIME,
    DECIMAL,
    FLOAT,
    INTEGER,
    JSON,
    NUMERIC,
    SMALLINT,
    TEXT,
    TIME,
    VARCHAR,
)
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from .base import Base, metadata


class User(Base, SerializerMixin):
    __tablename__ = "users"

    id = Column(INTEGER, primary_key=True, unique=True)
    username = Column(VARCHAR(254), unique=True)
    email = Column(VARCHAR(254), nullable=False, unique=True)
    password = Column(VARCHAR(1024), nullable=False)
    salt = Column(VARCHAR(512), nullable=False)
    resetToken = Column(VARCHAR(128), server_default=text("''"))
    displayName = Column(VARCHAR(512), server_default=text("''"))
    fallbackEmail = Column(VARCHAR(512), server_default=text("''"))
    source = Column(VARCHAR(128), server_default=text("''"))
    role = Column(VARCHAR(32), nullable=False)
    ts = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    creationTime = Column(
        TIMESTAMP, nullable=False, index=True, server_default=text("CURRENT_TIMESTAMP")
    )


class UserGroup(Base, SerializerMixin):
    __tablename__ = "userGroups"

    id = Column(VARCHAR(128), primary_key=True, unique=True)
    name = Column(VARCHAR(128), nullable=False, unique=True)
    source = Column(VARCHAR(128), server_default=text("''"))

    users = relationship(User, secondary="groupMembers")


t_groupMembers = Table(
    "groupMembers",
    metadata,
    #
    Column("groupId", ForeignKey(UserGroup.id), nullable=False),
    Column("userId", ForeignKey(User.id), nullable=False, index=True),
    #
    Index("groupId", "groupId", "userId", unique=True),
)
