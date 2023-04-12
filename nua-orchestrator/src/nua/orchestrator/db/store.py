"""Requests to backend DB.

Requests are full transactions, and mask the actual DB implementation to
the application.
"""
from copy import deepcopy
from datetime import datetime, timezone

from nua.lib.panic import warning

from .. import __version__ as nua_version
from .. import config
from ..app_instance import AppInstance
from ..constants import NUA_ORCH_ID, NUA_ORCHESTRATOR_TAG
from ..utils import image_size_repr, size_unit
from .model.auth import User
from .model.deployconfig import (
    ACTIVE,
    INACTIVE,
    PREVIOUS,
    DEPlOY_VALID_STATUS,
    DeployConfig,
)
from .model.image import Image
from .model.instance import RUNNING, STOPPED, Instance
from .model.setting import Setting
from .model.user_count import UserCount
from .session import Session

# from pprint import pformat


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
    as_mib = config.read("nua", "ui", "size_unit_MiB")
    images_list = []
    for img in list_images_raw():
        images_list.append(
            f"{img.id_sha[7:19]}  {img.nua_tag:<36}  {img.created}  "
            f"{image_size_repr(img.size, as_mib)}{size_unit(as_mib)}"
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


def installed_nua_settings() -> dict:
    """Return the dictionnary of settings of the nua-orchestrator.

    nua-orchestrator is not actually an app, but we use the settings
    facility to store its configuration in the DB with the app_id 'nua-
    orchestrator' (NUA_ORCH_ID).
    """
    with Session() as session:
        setting = (
            session.query(Setting).filter_by(app_id=NUA_ORCH_ID, instance="").first()
        )
        if not setting:
            return {}
        return setting.data or {}


def set_nua_settings(setting_dict):
    """Set the dictionnary of settings of the nua-orchestrator.

    nua-orchestrator is not actually an app, but we use the settings
    facility to store its configuration in the DB with the app_id 'nua-
    orchestrator'
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


def list_all_settings() -> list[dict]:
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


def store_instance(
    app_id="",
    nua_tag="",
    domain="",
    container="",
    image="",
    state=STOPPED,
    site_config=None,
):
    """Store a Nua instance in the local DB (table 'instance')."""

    new_instance = Instance(
        app_id=app_id,
        nua_tag=nua_tag,
        domain=domain,
        container=container,
        image=image,
        state=state,
        created=now_iso(),
        site_config=site_config or {},
    )
    with Session() as session:
        # Image:
        # enforce unicity
        existing = session.query(Instance).filter_by(domain=domain).first()
        if existing:
            session.delete(existing)
        session.flush()
        session.add(new_instance)
        session.commit()


def list_instances_all() -> list[Instance]:
    with Session() as session:
        return session.query(Instance).all()


# Not used ?
# def list_instances_all_short() -> list[str]:
#     result: list[str] = []
#     for instance in list_instances_all():
#         info = [
#             f"app_id: {instance.app_id}",
#             f"domain: {instance.domain}",
#             f"container: {instance.container}",
#             f"created: {instance.created}",
#             f"state: {instance.state}",
#         ]
#         result.append("\n".join(info))
#     return result


def list_instances_all_active() -> list:
    return [
        instance
        for instance in list_instances_all()
        if instance.state in {RUNNING, STOPPED}
    ]


def list_instances_container_running():
    return [inst.container for inst in list_instances_all() if inst.state == RUNNING]


def list_instances_container_local_active_volumes() -> list:
    """Return list of local mounted volumes.

    Volumes with properties:
    - required by active instances,
    - locally mounted ('local' driver), 'volume' type)
    - unique per 'source' key.

    A 'source' volume may be mounted on several instances. So, if still required by
    another instance, should not be unmounted when unmounting an instance.
    """
    volumes_dict = {}
    for instance in list_instances_all_active():
        # for volume in volumes_merge_config(instance.site_config):
        site = AppInstance(instance.site_config)

        # for volume in site.rebased_volumes_upon_nua_conf():
        for volume in site.volume:
            if volume["type"] == "volume" and volume.get("driver", "") == "local":
                _update_volumes_domains(volumes_dict, volume, instance.domain)
    return list(volumes_dict.values())


def _update_volumes_domains(volumes_dict: dict, volume: dict, domain: str):
    source = volume["source"]
    known_volume = volumes_dict.get(source, volume)
    domains = known_volume.get("domains", [])
    domains.append(domain)
    known_volume["domains"] = domains
    volumes_dict[source] = known_volume


def list_instances_container_active_volumes() -> list:
    """Return list of mounted volumes or binds.

    Volumes with properties:
    - required by active instances,
    - unique per 'source' key.

    A 'source' volume may be mounted on several instances. So, if still required by
    another instance, should not be unmounted when unmounting an instance.
    """
    volumes_dict = {}
    containers_dict = {}
    for instance in list_instances_all_active():
        # for volume in volumes_merge_config(instance.site_config):
        site = AppInstance.from_dict(instance.site_config)
        for volume in site.volume:
            if volume["type"] == "tmpfs":
                continue
            source = volume["source"]
            volumes_dict[source] = volume
            domains = containers_dict.get(source, [])
            domains.append(instance.domain)
            containers_dict[source] = domains
        for resource in site.resources:
            for volume in resource.volume:
                if volume["type"] == "tmpfs":
                    continue
                source = volume["source"]
                volumes_dict[source] = volume
                domains = containers_dict.get(source, [])
                domains.append(instance.domain)
                containers_dict[source] = domains

    for source, volume in volumes_dict.items():
        volume["domains"] = containers_dict[source]
    return list(volumes_dict.values())


def ports_instances_domains() -> dict[int, str]:
    """Return dict(port:domain) configured in instance, wether the instance is
    running or not."""
    used_domain_ports = {}
    for inst in list_instances_all():
        site_config = inst.site_config
        ports = site_config.get("port")  # a dict
        if ports:
            for port in ports.values():
                used_domain_ports[port["host_use"]] = site_config["domain"]
    return used_domain_ports


def instance_container(domain: str) -> str:
    with Session() as session:
        existing = session.query(Instance).filter_by(domain=domain).first()
        if existing:
            container = existing.container
        else:
            container = ""
        return container


def instance_delete_by_domain(domain: str):
    with Session() as session:
        session.query(Instance).filter_by(domain=domain).delete()
        session.commit()


def instance_delete_by_container(container: str):
    with Session() as session:
        session.query(Instance).filter_by(container=container).delete()
        session.commit()


def _fetch_instance_port_site(site_config: dict) -> int | None:
    ports = site_config.get("port")
    if not ports:
        return None
    for port in ports.values():
        proxy = port["proxy"]
        if proxy == "auto":
            return port["host_use"]
    return None


def instance_port(domain: str) -> int | None:
    """Return the (main?) instance port. Dubious.

    remarq: currently this function is unused
    """
    with Session() as session:
        existing = session.query(Instance).filter_by(domain=domain).first()
        if existing:
            site_config = existing.site_config
            port = site_config.get("host_use")
            if not port:
                port = _fetch_instance_port_site(site_config)
        else:
            port = None
        return port


def set_instance_container_state(domain: str, state: str):
    with Session() as session:
        existing = session.query(Instance).filter_by(domain=domain).first()
        if existing:
            existing.state = state
            session.commit()


def instance_persistent(domain: str, app_id: str) -> dict:
    """Return the persistent dictionary if (or an empty dict if not found)"""
    persistent = {}
    with Session() as session:
        existing = (
            session.query(Instance)
            .filter_by(
                domain=domain,
                app_id=app_id,
            )
            .first()
        )
        if existing:
            site_config = existing.site_config
            persistent = site_config.get("persistent", {})
    return persistent


def valid_deploy_config_state(state: str) -> str:
    if state in DEPlOY_VALID_STATUS:
        return state
    warning(f"invalid state for DeployConfig '{state}' replaced by 'INACTIVE'")
    return INACTIVE


def deploy_config_add_config(deploy_config: dict, previous_id: int, state: str) -> int:
    """Store a Nua deployment configuration in local DB (table 'deployconfig').

    Return:
        int: the id of the newly created record
    """
    state = valid_deploy_config_state(state)
    now = now_iso()
    record = DeployConfig(
        previous=previous_id,
        state=state,
        created=now,
        modified=now,
        deployed=deploy_config,
    )
    with Session() as session:
        session.add(record)
        session.commit()
        return record.id


def deploy_config_update_state(record_id: int, new_state: str):
    state = valid_deploy_config_state(new_state)
    now = now_iso()
    with Session() as session:
        existing = session.query(DeployConfig).filter_by(id=record_id).first()
        if existing:
            existing.state = state
            existing.modified = now
            session.commit()


def deploy_config_last_status(status: str, limit: int = 2) -> list:
    """retrieve the config with "active" state.

    It should be only one.
    """
    if status and status in DEPlOY_VALID_STATUS:
        return _deploy_config_last_status(status, limit)
    else:
        return _deploy_config_last_any(limit)


def _deploy_config_last_status(status: str, limit: int) -> list:
    with Session() as session:
        records = (
            session.query(DeployConfig)
            .filter_by(state=status)
            .order_by(DeployConfig.id.desc())
            .limit(limit)
        )
        if records:
            return [rec.to_dict() for rec in records]
        return []


def _deploy_config_last_any(limit: int) -> list:
    with Session() as session:
        records = (
            session.query(DeployConfig).order_by(DeployConfig.id.desc()).limit(limit)
        )
        if records:
            return [rec.to_dict() for rec in records]
        return []


def deploy_config_active() -> dict:
    """retrieve the config with "active" state.

    It should be only one.
    """
    items = deploy_config_last_status(ACTIVE, 1)
    if items:
        return items[0]
    return {}


def deploy_config_previous() -> dict:
    """retrieve the config with "previous" state.

    It should be zero, or sometimes only one.
    """
    items = deploy_config_last_status(PREVIOUS, 1)
    if items:
        return items[0]
    return {}


def deploy_config_last_inactive() -> dict:
    """retrieve the last config with "inactive" state."""
    items = deploy_config_last_status(INACTIVE, 1)
    if items:
        return items[0]
    return {}


def deploy_config_last_one() -> dict:
    """Retrieve the last deployment config."""
    items = _deploy_config_last_any(1)
    if items:
        return items[0]
    return {}


def new_user_number() -> int:
    """Return incremented value of UserCount."""
    with Session() as session:
        ucount = session.query(UserCount).first()
        if ucount:
            ucount.counter += 1
        else:
            ucount = UserCount()
            ucount.counter = 1
            session.add(ucount)
        session.commit()
        return ucount.counter
