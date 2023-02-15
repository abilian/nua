from sqlalchemy import Column, Integer, String
from sqlalchemy_serializer import SerializerMixin

from .base import Base


class Image(Base, SerializerMixin):
    """A Docker image managed by Nua.

    Map of some docker image parameters and Nua tags.
        id_sha: docker id of image, "sha256:abc123..."
        nua_tag: full Nua tag: "nua-apache-basic:2.4.52-2"
        app_id: id of the Nua app: "apache-basic"
        nua_version: version of Nua that created the image: "0.1.38"
        created: date creation, iso format, local: "2022-06-14T15:22:11"
        size: size in bytes

        FIXME: created to be improved with tz info)
    """

    __tablename__ = "image"

    id_sha = Column(String(80), primary_key=True, unique=True)
    nua_tag = Column(String(80), primary_key=True, unique=True)
    app_id = Column(String(80))
    nua_version = Column(String(20))
    created = Column(String(40))
    size = Column(Integer)

    def __repr__(self) -> str:
        return f"Image(sha={self.id_sha[7:13]}, tag={self.nua_tag}"
