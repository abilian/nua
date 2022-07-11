from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from .base import Base, metadata


class User(Base, SerializerMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, unique=True)
    username = Column(String(254), unique=True)
    email = Column(String(254), nullable=False, unique=True)
    password = Column(String(1024), nullable=False)
    salt = Column(String(512), nullable=False)
    reset_token = Column(String(128), server_default=text("''"))
    display_name = Column(String(512), server_default=text("''"))
    fallback_mail = Column(String(512), server_default=text("''"))
    source = Column(String(128), server_default=text("''"))
    role = Column(String(32), nullable=False)
    data = Column(JSON)
    ts = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    creation_time = Column(
        TIMESTAMP, nullable=False, index=True, server_default=text("CURRENT_TIMESTAMP")
    )


class UserGroup(Base, SerializerMixin):
    __tablename__ = "userGroups"

    id = Column(String(128), primary_key=True, unique=True)
    name = Column(String(128), nullable=False, unique=True)
    source = Column(String(128), server_default=text("''"))

    users = relationship(User, secondary="groupMembers")


t_group_members = Table(
    "groupMembers",
    metadata,
    #
    Column("groupId", ForeignKey(UserGroup.id), nullable=False),
    Column("userId", ForeignKey(User.id), nullable=False, index=True),
    #
    Index("groupId", "groupId", "userId", unique=True),
)
