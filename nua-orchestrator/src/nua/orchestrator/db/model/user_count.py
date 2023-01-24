from sqlalchemy import Column, Integer
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class UserCount(Base, SerializerMixin):
    """Table to store the user count information.

    Usage: increment counter to create a unique user id.
    """

    __tablename__ = "user_count"

    id = Column(Integer, primary_key=True, unique=True)
    counter = Column(Integer)
