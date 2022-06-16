"""Requests to bakend DB."""
from ..constants import NUA_BASE_TAG
from ..docker_utils import image_size_repr, size_unit
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
        session.flush()
        session.add(new_image)
        session.commit()


def list_images_raw():
    with Session() as session:
        return session.query(Image).all()


def list_images_ids():
    return [img.id_sha for img in list_images_raw()]


def list_images():
    images_list = []
    for img in list_images_raw():
        images_list.append(
            f"{img.id_sha[7:19]}  {img.nua_tag:<40}  {img.created} "
            f" {image_size_repr(img.size)}{size_unit()}"
        )
    return images_list


def available_images():
    """Docker images ready to be mounted by Nua."""
    internals = {"nua-min", "nua-base"}
    with Session() as session:
        images = session.query(Image).all()
        return [i for i in images if i.app_id not in internals]


def remove_ids(ids_list):
    with Session() as session:
        session.query(Image).filter(Image.id_sha.in_(ids_list)).delete()
        session.commit()


def images_id_per_app_id(app_id):
    with Session() as session:
        images = session.query(Image).filter_by(app_id=app_id).all()
        return [img.id_sha for img in images]


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


def dump_all_settings() -> str:
    with Session() as session:
        settings = session.query(Setting).all()
        return [s.to_dict() for s in settings]


def set_app_settings(app_id, setting_dict):
    with Session() as session:
        # we cant be sure of situation or backend, let's be rough
        instance = setting_dict.get("instance", "")
        session.query(Setting).filter(
            Setting.app_id == app_id, Setting.instance == instance
        ).delete()
        session.flush()
        new_setting = Setting(
            app_id=app_id,
            nua_tag=NUA_BASE_TAG,
            instance=instance,
            data=setting_dict,
        )
        session.add(new_setting)
        session.commit()


def set_nua_settings(setting_dict):
    set_app_settings("nua-base", setting_dict)


#
# def set_app_one_setting(app_id, instance, key, value):
#     with Session() as session:
#         # we cant be sure of situation or backend, let's be rough
#         current = (
#             session.query(Setting)
#             .filter(Setting.app_id == app_id, Setting.instance == instance)
#             .first()
#         )
#         if not current:
#             raise ValueError(
#                 f"set_app_one_setting(): '{app_id}'/'{instance}' not found in Setting table."
#             )
#         current
#         new_setting = Setting(
#             app_id=app_id,
#             nua_tag=NUA_BASE_TAG,
#             instance=setting_dict.get("instance", ""),
#             data=setting_dict,
#         )
#         session.add(new_setting)
#         session.commit()
#
#
# def set_nua_settings(setting_dict):
#     set_app_settings("nua-base", setting_dict)
