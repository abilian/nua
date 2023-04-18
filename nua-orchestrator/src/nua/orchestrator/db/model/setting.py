from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from .base import Base


# TODO: rename to "Settings" (plural)
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

    # TODO add constaints
    id: Mapped[int] = mapped_column(primary_key=True)
    app_id: Mapped[str] = mapped_column(default="")
    nua_tag: Mapped[str] = mapped_column(default="")
    instance: Mapped[str] = mapped_column(default="")
    activation: Mapped[str] = mapped_column(default="")

    # active = Column(Boolean, nullable=True, default=False)
    # container = Column(String(80), default="")
    data: Mapped[JSON] = mapped_column(JSON, default={})

    #  broken for sqlite: instance = index_property("data", "instance", default="")

    def __repr__(self) -> str:
        return f"Setting(app_id={self.app_id}, instance='{self.instance}', tag={self.nua_tag})"
