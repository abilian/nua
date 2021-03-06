"""Requests to backend DB.

Requests are full transactions, and mask the actual DB implementation to
the application.
"""
from copy import deepcopy

from .. import __version__ as nua_version
from ..constants import NUA_ORCH_ID, NUA_ORCHESTRATOR_TAG
from ..docker_utils import image_size_repr, size_unit
from .model.auth import User
from .model.image import Image
from .model.setting import Setting
from .session import Session


def get_image_by_nua_tag(tag):
    """Find a Nua image in the local DB by Nua id."""
    with Session() as session:
        return session.query(Image).filter_by(nua_tag=tag).first()


def store_image(
    id_sha="",
    app_id="",
    nua_tag="",
    created="",
    size=0,
    nua_version=nua_version,
    instance="",
    data=None,
):
    """Store a Nua image in the local DB (table 'image').

    Also set the initial settings of the image in the 'setting' table.
    """
    new_image = Image(
        id_sha=id_sha,
        app_id=app_id,
        nua_tag=nua_tag,
        created=created,
        size=size,
        nua_version=nua_version,
    )
    with Session() as session:
        # Image:
        # enforce unicity
        existing = session.query(Image).filter_by(nua_tag=nua_tag).first()
        if existing:
            session.delete(existing)
        existing = session.query(Image).filter_by(id_sha=id_sha).first()
        if existing:
            session.delete(existing)
        session.flush()
        session.add(new_image)
        # Setting:
        _set_app_settings(
            session,
            app_id,
            nua_tag,
            instance,
            activation="docker",
            # active=False,
            # container="",
            setting_dict=data,
        )
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
            f"{img.id_sha[7:19]}  {img.nua_tag:<36}  {img.created}  "
            f"{image_size_repr(img.size)}{size_unit()}"
        )
    return images_list


def list_available_images():
    """Docker images ready to be mounted by Nua."""
    internals = {"nua-python", "nua-builder"}
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
    """Return the dictionnary of settings of the nua-orchestrator.

    nua-orchestrator is not actually an app, but we use the settings facility
    to store its configuration in the DB with the app_id 'nua-orchestrator'
    (NUA_ORCH_ID).
    """
    with Session() as session:
        setting = (
            session.query(Setting).filter_by(app_id=NUA_ORCH_ID, instance="").first()
        )
        if not setting:
            return None
        return setting.data


def set_nua_settings(setting_dict):
    """Set the dictionnary of settings of the nua-orchestrator.

    nua-orchestrator is not actually an app, but we use the settings facility
    to store its configuration in the DB with the app_id 'nua-orchestrator'
    """
    set_app_settings(NUA_ORCH_ID, NUA_ORCHESTRATOR_TAG, "", setting_dict)


def installed_nua_version():
    """Return the version of 'nua-orchestrator' stored in the DB settings."""
    with Session() as session:
        setting = (
            session.query(Setting).filter_by(app_id=NUA_ORCH_ID, instance="").first()
        )
        if not setting:
            return None
        return setting.data.get("nua_version", "")


def list_all_settings() -> str:
    with Session() as session:
        settings = session.query(Setting).all()
        return [s.to_dict() for s in settings]


def _set_app_settings(
    session,
    app_id,
    nua_tag,
    instance,
    activation,
    # active=False,
    # container="",
    setting_dict=None,
):
    # fixme: not sure if storing instance in conf data, but seems more natural
    # we cant be sure of situation or backend, let's be rough
    setting_dict = setting_dict or {}
    instance = instance or setting_dict.get("instance", "")
    session.query(Setting).filter(
        Setting.app_id == app_id, Setting.instance == instance
    ).delete()
    session.flush()
    new_setting = Setting(
        app_id=app_id,
        nua_tag=nua_tag,
        instance=instance,
        activation=activation,
        # active=active,
        # container=container,
        data=setting_dict,
    )
    session.add(new_setting)


def set_app_settings(app_id, nua_tag, instance, setting_dict):
    with Session() as session:
        _set_app_settings(
            session, app_id, nua_tag, instance, "docker", setting_dict=setting_dict
        )
        session.commit()


def stored_user_data(username: str):
    """Return the dictionnary "data" of the user."""
    with Session() as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None
        return deepcopy(user.data)


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
#             nua_tag=NUA_BUILDER_TAG,
#             instance=setting_dict.get("instance", ""),
#             data=setting_dict,
#         )
#         session.add(new_setting)
#         session.commit()
#
#
