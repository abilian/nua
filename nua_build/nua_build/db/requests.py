import json

from ..constants import NUA_BASE_TAG
from .model.image import Image
from .model.setting import Setting
from .session import Session


def find_image_nua_tag(tag):
    """Find a Nua image in the local DB by Nua id."""
    with Session() as session:
        return session.query(Image).filter_by(nua_tag=tag).first()


def store_image(id_sha="", nua_tag="", app_id="", created="", size=0, nua_version=""):
    """Store a Nua image in the local DB."""
    new_image = Image(
        id_sha=id_sha,
        nua_tag=nua_tag,
        app_id=app_id,
        created=created,
        size=size,
        nua_version=nua_version,
    )
    with Session() as session:
        # enforce unicity
        existing = session.query(Image).filter_by(nua_tag=nua_tag).first()
        if existing:
            session.delete(existing)
        existing = session.query(Image).filter_by(id_sha=id_sha).first()
        if existing:
            session.delete(existing)
        session.add(new_image)
        session.commit()


def print_images():
    """Print all Nua images."""
    with Session() as session:
        images = session.query(Image).all()
        for img in images:
            print(
                f"{img.id_sha[7:15]}  {img.nua_tag:<40}  {img.created}  {img.size}MiB"
            )


def available_images():
    """Docker images ready to be mounted by Nua."""
    internals = {"nua-min", "nua-base"}
    with Session() as session:
        images = session.query(Image).all()
        return [i for i in images if i.app_id not in internals]


def installed_nua_settings():
    with Session() as session:
        setting = (
            session.query(Setting).filter_by(app_id="nua-base", instance="").first()
        )
        if not setting:
            return None
        return setting.data


def installed_nua_version():
    with Session() as session:
        setting = (
            session.query(Setting).filter_by(app_id="nua-base", instance="").first()
        )
        if not setting:
            return None
        return setting.data.get("nua_version", "")


def dump_settings() -> str:
    with Session() as session:
        settings = session.query(Setting).all()
        return json.dumps(
            [s.to_dict() for s in settings],
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )


def set_nua_settings(setting_dict):
    with Session() as session:
        # we cant be sure of situation or backend, let's be rough
        session.query(Setting).filter(
            Setting.app_id == "nua-base", Setting.instance == ""
        ).delete()
        new_setting = Setting(
            app_id="nua-base",
            nua_tag=NUA_BASE_TAG,
            instance=setting_dict.get("instance", ""),
            data=setting_dict,
        )
        session.add(new_setting)
        session.commit()
