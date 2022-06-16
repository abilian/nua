from sqlalchemy import JSON, TIMESTAMP, Column, Index, Integer, String, text
from sqlalchemy.ext.indexable import index_property
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class Setting(Base, SerializerMixin):
    """The settings of an instance of an app.

    Instance "" for the base settings of the app. Contains a JSON data
    representation of actual values. index key: app_instance.
    app_instance is "something", default to "" for base settings (and/or
    build settings). nua_tag permits to find the related docker image.
    """

    __tablename__ = "setting"

    id = Column(Integer, primary_key=True)
    app_id = Column(String(80))
    nua_tag = Column(String(80))
    instance = Column(String(80), default="")
    data = Column(JSON)
    #  broken for sqlite: instance = index_property("data", "instance", default="")

    def __repr__(self):
        return f"Setting(app_id={self.app_id}, instance='{self.instance}', tag={self.nua_tag})"
