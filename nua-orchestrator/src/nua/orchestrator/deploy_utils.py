"""Class to manage the deployment of a group of AppInstance."""
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from typing import Any

import docker
import docker.types
from docker.models.containers import Container
from nua.lib.archive_search import ArchiveSearch
from nua.lib.docker import display_one_docker_img, docker_require
from nua.lib.panic import Abort, important, info, show, vprint, warning
from nua.lib.tool.state import verbosity

from .app_instance import AppInstance
from .db import store
from .docker_utils import (  # docker_volume_prune,
    docker_exec_commands,
    docker_host_gateway_ip,
    docker_network_create_bridge,
    docker_network_prune,
    docker_network_remove_one,
    docker_pause_container_name,
    docker_remove_container_previous,
    docker_remove_volume_by_source,
    docker_restart_container_name,
    docker_run,
    docker_service_start_if_needed,
    docker_start_container_name,
    docker_stop_container_name,
    docker_unpause_container_name,
    docker_volume_create_or_use,
    docker_volume_type,
    docker_wait_for_status,
)
from .internal_secrets import secrets_dict
from .net_utils.ports import check_port_available
from .provider import Provider
from .utils import size_to_bytes
from .volume import Volume

PULLED_IMAGES: dict[str, str] = {}


def load_install_image(image_path: str | Path) -> tuple:
    """Install docker image (tar file) in local docker daemon.

    Return: tuple(image_id, image_nua_config)
    """
    path = Path(image_path)
    # image is local, so we can mount it directly
    if not path.is_file():
        warning("Local Docker image does not exist")
        raise FileNotFoundError(path)

    arch_search = ArchiveSearch(path)
    image_nua_config = arch_search.get_nua_config_dict()
    if not image_nua_config:
        raise Abort(
            f"image non compatible Nua: {path}.", explanation="No Nua config found"
        )

    metadata = image_nua_config["metadata"]
    msg = "Installing App: {id} {version}, {title}".format(**metadata)
    if verbosity(0):
        important(msg)

    client = docker.from_env()
    # images_before = {img.id for img in client.images.list()}
    with open(path, "rb") as input:  # noqa: S108
        loaded = client.images.load(input)
    if not loaded or len(loaded) > 1:
        warning("loaded image result is strange:", f"{loaded=}")
    loaded_img = loaded[0]
    # images_after = {img.id for img in client.images.list()}
    # new = images_after - images_before
    with verbosity(0):
        important("Installing image:")
        display_one_docker_img(loaded_img)
    return loaded_img.id, image_nua_config


def port_allocator(start_ports: int, end_ports: int, allocated_ports: set) -> Callable:
    def allocator() -> int:
        # O(n2), but very few ports to configure
        for port in range(start_ports, end_ports):
            if port not in allocated_ports and check_port_available(
                "127.0.0.1", str(port)
            ):
                allocated_ports.add(port)
                return port
        raise Abort("Not enough available ports")

    return allocator


def mount_provider_volumes(volumes: list[dict[str, Any]]) -> list:
    create_docker_volumes(volumes)
    mounted_volumes = []
    for volume_params in volumes:
        mounted_volumes.append(new_docker_mount(volume_params))
    return mounted_volumes


def extra_host_gateway() -> dict:
    """Sent an update for docker parameters 'extra_hosts':

    host.docker.internal.
    """
    return {"host.docker.internal": docker_host_gateway_ip()}


def unused_volumes(orig_mounted_volumes: list[Volume]) -> list[Volume]:
    current_mounted = store.list_instances_container_active_volumes()
    current_sources = {vol.full_name for vol in current_mounted}
    return [vol for vol in orig_mounted_volumes if vol.full_name not in current_sources]


def create_docker_volumes(volumes_config: list):
    for volume_params in volumes_config:
        docker_volume_create_or_use(volume_params)


def remove_volume_by_source(source: str):
    if not source:
        return
    info(f"Removing volume: {source}")
    docker_remove_volume_by_source(source)


def new_docker_mount(volume_params: dict) -> docker.types.Mount:
    volume = Volume.parse(volume_params)
    if volume.is_managed:
        driver_config = new_docker_driver_config(volume)
    else:
        driver_config = None
    volume_type = docker_volume_type(volume)
    read_only = bool(volume.options.get("read-only", False))
    if volume.type == "tmpfs":
        tmpfs_size = size_to_bytes(volume.options.get("tmpfs_size")) or None
        tmpfs_mode = volume.options.get("tmpfs_mode") or None
    else:
        tmpfs_size, tmpfs_mode = None, None

    return docker.types.Mount(
        volume.target,
        volume.full_name or None,
        volume_type,
        driver_config=driver_config,
        read_only=read_only,
        tmpfs_size=tmpfs_size,
        tmpfs_mode=tmpfs_mode,
    )


def new_docker_driver_config(volume: Volume) -> docker.types.DriverConfig | None:
    """Volume driver configuration for Docker.

    Only valid for the 'volume' type.
    """
    if not volume.driver or volume.driver in {"local", "docker"}:
        return None
    # to be completed
    return docker.types.DriverConfig(volume.driver)


# def unmount_unused_volumes(orig_mounted_volumes: list):
#     for unused in unused_volumes(orig_mounted_volumes):
#         docker_volume_prune(unused)


def start_one_container(rsite: Provider, mounted_volumes: list):
    run_params = rsite.run_params
    if mounted_volumes:
        run_params["mounts"] = mounted_volumes
    rsite.run_params = run_params
    with verbosity(4):
        vprint(f"start_one_container() run_params:\n{pformat(run_params)}")
    secrets = secrets_dict(rsite.requested_secrets)
    new_container = docker_run(rsite, secrets)
    rsite.container_id = new_container.id
    if mounted_volumes:
        rsite.run_params["mounts"] = True
    with verbosity(0):
        info(f"    -> container of name: {rsite.container_name}")
        info(f"            container id: {rsite.container_id_short}")
        if rsite.network_name:
            info(f"    connected to network: {rsite.network_name}")
    exec_post_run(rsite, new_container)


def exec_post_run(
    rsite: Provider,
    container: Container,
    expected: str = "running",
    timeout: int = 60,
) -> None:
    if not rsite.post_run:
        return
    expected = rsite.post_run_status or "running"
    status_ok = docker_wait_for_status(container, expected, timeout)
    if not status_ok:
        raise RuntimeError("Unable to exec post-run command")
    with verbosity(1):
        show("Executing the post-run commands")
    commands = post_run_expanded(rsite)
    docker_exec_commands(container, commands)


def post_run_expanded(rsite: Provider) -> list[str]:
    data = run_time_exec_data(rsite)
    return [line.format(**data) for line in rsite.post_run]


def run_time_exec_data(rsite: Provider) -> dict[str, Any]:
    orig = deepcopy(rsite.nua_config["metadata"])
    orig["label"] = rsite.label_id
    orig["domain"] = rsite.domain
    orig["hostname"] = rsite.hostname
    data = {}
    for key, val in deepcopy(orig).items():
        if isinstance(val, str):
            data[key] = val.format(**orig)
        else:
            data[key] = val
    data.update(rsite.env)
    return data


def stop_one_app_containers(app: AppInstance):
    stop_one_container(app)
    for provider in app.providers:
        stop_one_container(provider)
    # docker_network_prune() : no, need to keep same network to easily restart the
    # container with same network.


def pause_one_app_containers(app: AppInstance):
    pause_one_container(app)
    for provider in app.providers:
        pause_one_container(provider)


def unpause_one_app_containers(app: AppInstance):
    unpause_one_container(app)
    for provider in app.providers:
        unpause_one_container(provider)


def start_one_app_containers(app: AppInstance):
    for provider in app.providers:
        start_one_deployed_container(provider)
    start_one_deployed_container(app)


def restart_one_app_containers(app: AppInstance):
    for provider in app.providers:
        restart_one_deployed_container(provider)
    restart_one_deployed_container(app)


def stop_one_container(rsite: Provider):
    with verbosity(0):
        info(f"    -> stop container of name: {rsite.container_name}")
        info(f"                 container id: {rsite.container_id_short}")
    stop_containers([rsite.container_name])


def pause_one_container(rsite: Provider):
    with verbosity(0):
        info(f"    -> pause container of name: {rsite.container_name}")
        info(f"                  container id: {rsite.container_id_short}")
    pause_containers([rsite.container_name])


def unpause_one_container(rsite: Provider):
    with verbosity(0):
        info(f"    -> unpause container of name: {rsite.container_name}")
        info(f"                    container id: {rsite.container_id_short}")
    unpause_containers([rsite.container_name])


def stop_containers(container_names: list[str]):
    for name in container_names:
        if not name:
            continue
        docker_stop_container_name(name)


def pause_containers(container_names: list[str]):
    for name in container_names:
        if not name:
            continue
        docker_pause_container_name(name)


def unpause_containers(container_names: list[str]):
    for name in container_names:
        if not name:
            continue
        docker_unpause_container_name(name)


def start_one_deployed_container(rsite: Provider):
    with verbosity(0):
        info(f"    -> start container of name: {rsite.container_name}")
        info(f"                  container id: {rsite.container_id_short}")
    start_containers([rsite.container_name])


def restart_one_deployed_container(rsite: Provider):
    with verbosity(0):
        info(f"    -> restart container of name: {rsite.container_name}")
        info(f"                    container id: {rsite.container_id_short}")
    restart_containers([rsite.container_name])


def start_containers(container_names: list[str]):
    for name in container_names:
        if not name:
            continue
        docker_start_container_name(name)


def restart_containers(container_names: list[str]):
    for name in container_names:
        if not name:
            continue
        docker_restart_container_name(name)


def deactivate_containers(container_names: list[str], show_warning: bool = True):
    for name in container_names:
        if not name:
            continue
        docker_remove_container_previous(name, show_warning)
        store.instance_delete_by_container(name)


def deactivate_app(app: AppInstance):
    """Deactive containers of AppInstance and all sub Providers (updating
    orchestrator DB)."""
    container_names = [res.container_name for res in app.providers]
    container_names.append(app.container_name)
    deactivate_containers(container_names, show_warning=False)


def deactivate_all_instances():
    """Find all instances in DB.

    - remove container if it exists
    - remove site from DB
    """
    for instance in store.list_instances_all():
        with verbosity(1):
            msg = f"Removing instance '{instance.app_id}' on '{instance.domain}'"
            info(msg)
        site_config = instance.site_config
        providers_list = site_config.get("providers") or []
        container_names = [res.get("container_name", "") for res in providers_list]
        container_names.append(site_config.get("container_name", ""))
        container_names = [name for name in container_names if name]
        deactivate_containers(container_names)
    docker_network_prune()


def start_container_engine():
    """Ensure the containr system is running.

    Currrently: only checking that Docker daemon is up.
    """
    docker_service_start_if_needed()


def create_container_private_network(network_name: str):
    """Create a private network for the container (and it's sub containers).

    Currrently: only managing Docker bridge network.
    """
    if not network_name:
        return
    docker_network_create_bridge(network_name)


def remove_container_private_network(network_name: str):
    """Remove an existing private network.

    Currrently: only managing Docker bridge network.
    """
    if not network_name:
        return
    docker_network_remove_one(network_name)


def pull_provider_container(provider: Provider) -> bool:
    """Retrieve a provider container or get reference from cache.

    Currrently: only managing Docker bridge network.
    """
    # print("======================================")
    # print(pformat(provider))
    # print("======================================")
    docker_url = provider.base_image()
    if docker_url:
        provider.image = docker_url
    if not provider.image:
        return True
    return _pull_provider_docker(provider)


def _pull_provider_docker(provider: Provider) -> bool:
    """Retrieve a provider container or get reference from cache."""
    if provider.image not in PULLED_IMAGES:
        _actual_pull_container(provider)

    if provider.image not in PULLED_IMAGES:
        warning(f"No image found for '{provider.image}'")
        return False

    provider.image_id = PULLED_IMAGES[provider.image]
    return True


def _actual_pull_container(provider: Provider):
    """Retrieve a provider container."""
    with verbosity(0):
        info(f"Pulling image '{provider.image}'")

    docker_image = docker_require(provider.image)
    if docker_image:
        PULLED_IMAGES[provider.image] = docker_image.id
        with verbosity(0):
            display_one_docker_img(docker_image)
