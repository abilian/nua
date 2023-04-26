from datetime import datetime

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from .base import Base

RUNNING = "started"
STOPPED = "stopped"


class Instance(Base, SerializerMixin):
    """The deployed instance of an app.

    - id: system generated colum for indexes
    - app_id: nua id of the app
    - nua_tag: nua tag, "nua-{app_id}:{version}-{release}". nua_tag permits
      to find the related docker image.
    - domain: domain serving the app
    - container: name of the deployed contaner if image started (or "")
    - image: name of the docker image (if docker deployed)
    - state: one of "running" "stopped"
    - site_config: JSON data representation of actual deployment config
      values, including the instance nginx domain.

     {'host_use': 8109,
      'container': 'nua-flask-upload-one-1.0-1-sloop.example.com',
      'domain': 'sloop.example.com/xxx',
      'image': 'nua-flask-upload-one:1.0-1',
      'image_id': 'sha256:232d921796c7f62f9240d8727d39829d31772a395d5c060ece5c74a6315b2f0e',
      'image_nua_config': {'build': {'document_root': '/nua/app/html'},
                           'instance': {'port': 5100, domain...},
                           'metadata': {'author': 'Nua testers',
                                        'id': 'flask-upload-one',
                                        'licence': 'MIT',
                                        'profile': ['test'],
                                        'release': 1,
                                        'tagline': 'Nua test with Flask and mount '
                                                   '- one',
                                        'tags': ['test',
                                                 'html',
                                                 'web',
                                                 'static',
                                                 'mount'],
                                        'title': 'Flask test upload one',
                                        'version': '1.0',
                                        'website': 'https://nua.rocks/'},
                           'docker': {'auto_remove': True,
                                   'detach': True,
                                   'mem_limit': '1G',
                                   'mounts': [{'ReadOnly': False,
                                               'Source': 'flask_uploads',
                                               'Target': '/var/tmp/uploads',
                                               'Type': 'volume'}],
                                   'name': 'nua-flask-upload-one-1.0-1-sloop.example.com',
                                   'ports': {'80/tcp': 8109}},
                           'env': {},
                           'volume': [{'driver': 'local',
                                       'dst': '/var/tmp/uploads',
                                       'name': 'flask_uploads',
                                       'type': 'volume'}]},
      'port': 'auto',
      'run_params': {'auto_remove': True,
                     'detach': True,
                     'mem_limit': '1G',
                     'mounts': [{'ReadOnly': False,
                                 'Source': 'flask_uploads',
                                 'Target': '/var/tmp/uploads',
                                 'Type': 'volume'}],
                     'name': 'nua-flask-upload-one-1.0-1-sloop.example.com',
                     'ports': {'80/tcp': 8109}}}

    There can be only one app per domain.
    """

    __tablename__ = "instance"

    # TODO: add constraints
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[str] = mapped_column(String(80), default="")
    label_id: Mapped[str] = mapped_column(String(80), default="")
    nua_tag: Mapped[str] = mapped_column(String(160), default="")
    domain: Mapped[str] = mapped_column(String(160), default="")
    container: Mapped[str] = mapped_column(String(160), default="")
    image: Mapped[str] = mapped_column(String(160), default="")
    state: Mapped[str] = mapped_column(String(16), default=STOPPED)
    created: Mapped[datetime] = mapped_column(default=datetime.now)
    site_config: Mapped[JSON] = mapped_column(JSON, default={})

    #  broken for sqlite: instance = index_property("data", "instance", default="")

    def __repr__(self) -> str:
        return (
            f"Instance(label_id={self.label_id}, app_id={self.app_id}, "
            f"container='{self.container}', tag={self.nua_tag})"
        )
