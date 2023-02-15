from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class Setting(Base, SerializerMixin):
    """The settings of an instance of an app.

    - id: system generated colum for indexes
    - app_id: nua id of the app
    - nua_tag: nua tag, "nua-{app_id}:{version}-{release}". nua_tag permits
      to find the related docker image.
    - instance: "" for the base settings of the app. "local" for
      runnning/installed nua-build software. User choice for others.
    - activation: "docker" or "system" for the moment. How this app service
      is installed
    # bad idea - active: bool, wether these settings are applied on a currently running
      instance (either local or dockerised or other)
    # - container: for "docker" installation app, "" or the id of the active
      container.
    - data: ontains a JSON data representation of actual config values. For
      raw "" instance, it is the original nua-config.toml content.
    """

    __tablename__ = "setting"

    id = Column(Integer, primary_key=True)
    app_id = Column(String(80))
    nua_tag = Column(String(80))
    instance = Column(String(80), default="")
    activation = Column(String(80), default="")
    # active = Column(Boolean, nullable=True, default=False)
    # container = Column(String(80), default="")
    data = Column(JSON)
    #  broken for sqlite: instance = index_property("data", "instance", default="")

    def __repr__(self) -> str:
        return f"Setting(app_id={self.app_id}, instance='{self.instance}', tag={self.nua_tag})"
