from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class Instance(Base, SerializerMixin):
    """The deployed instance of an app.

    - id: system generated colum for indexes
    - app_id: nua id of the app
    - nua_tag: nua tag, "nua-{app_id}:{version}-{release}". nua_tag permits
      to find the related docker image.
    - domain: domain serving the app
    - prefix: if several instances on a domain, instance prefix (or "")
    - container: name of the deployed contaner if image started (or "")
    - image: name of the docker image (if docker deployed)
    - state: one of "running" "stopped"
    - deploy_config: JSON data representation of actual deployment config
      values, including the instance prefix and/or nginx domain.
      (deploy_config is ~ web site instance config)
    # - docker_config: JSON data representation of deploy config as passed to
    #   docker (so with actual port)
    - nua_config: JSON data representation of original package configuration

    There can be only one app per domain/prefix.
    """

    RUNNING = "running"
    STOPPED = "stopped"

    __tablename__ = "instance"

    id = Column(Integer, primary_key=True)
    app_id = Column(String(80))
    nua_tag = Column(String(160))
    domain = Column(String(160))
    prefix = Column(String(160))
    container = Column(String(160), default="")
    image = Column(String(160), default="")
    state = Column(String(16), default=STOPPED)
    created = Column(String(40))
    deploy_config = Column(JSON)
    # docker_config = Column(JSON)
    nua_config = Column(JSON)
    #  broken for sqlite: instance = index_property("data", "instance", default="")

    def __repr__(self):
        return f"Instance(app_id={self.app_id}, container='{self.container}', tag={self.nua_tag})"
