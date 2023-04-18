from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped, mapped_column
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

    id_sha: Mapped[str] = mapped_column(String(80), primary_key=True, unique=True)
    nua_tag: Mapped[str] = mapped_column(String(80), primary_key=True, unique=True)
    app_id: Mapped[str] = mapped_column(String(80), default="")
    nua_version: Mapped[str] = mapped_column(String(20), default="")
    created: Mapped[str] = mapped_column(String(40), default="")
    size: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"Image(sha={self.id_sha[7:13]}, tag={self.nua_tag}"
