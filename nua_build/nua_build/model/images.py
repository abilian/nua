from sqlalchemy import TIMESTAMP, Column, Index, Integer, String, text
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from .base import Base, metadata


class Images(Base, SerializerMixin):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    id_sha = Column(String(80), unique=True)
    nua_id = Column(String(80))
    nua_tag = Column(String(80))
    nua_version = Column(String(20))
    created = Column(String(40))
    size = Column(Integer)

    def __repr__(self):
        return f"Images(id={self.id!r}, sha={self.id_sha[7:13]}, tag={self.nua_tag}"
