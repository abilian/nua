"""class to manage the deployment of a group os sites."""
from collections.abc import Callable
from pathlib import Path
from pprint import pformat

import docker
import docker.types
from nua.autobuild.docker_build_utils import display_one_docker_img, docker_require
from nua.lib.console import print_green, print_magenta
from nua.lib.panic import error, info, warning
from nua.lib.tool.state import verbosity

from .archive_search import ArchiveSearch
from .db import store
from .docker_utils import (
    docker_host_gateway_ip,
    docker_network_create_bridge,
    docker_network_prune,
    docker_remove_container_previous,
    docker_run,
    docker_service_start_if_needed,
    docker_volume_create_or_use,
    docker_volume_prune,
)
from .internal_secrets import secrets_dict
from .resource import Resource
from .server_utils.net_utils import check_port_available
from .site import Site
from .utils import size_to_bytes
from .volume import Volume


def load_install_image(image_path: str | Path) -> tuple:
    """Install docker image (tar file) in local docker daeon.

    Return: tuple(image_id, image_nua_config)
    """
    path = Path(image_path)
    # image is local, so we can mount it directly
    if not path.is_file():
        warning("Local Docker image does not exist")
        raise FileNotFoundError(path)
    arch_search = ArchiveSearch(path)
    image_nua_config = arch_search.nua_config_dict()
    if not image_nua_config:
        error(f"image non compatible Nua: {path}.", explanation="No Nua config found")
    metadata = image_nua_config["metadata"]
    msg = "Installing App: {id} {version}, {title}".format(**metadata)
    print_magenta(msg)
    client = docker.from_env()
    # images_before = {img.id for img in client.images.list()}
    with open(path, "rb") as input:  # noqa: S108
        loaded = client.images.load(input)
    if not loaded or len(loaded) > 1:
        warning("loaded image result is strange:", f"{loaded=}")
    loaded_img = loaded[0]
    # images_after = {img.id for img in client.images.list()}
    # new = images_after - images_before
    if verbosity(1):
        print_green("Intalled image:")
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
        error("Not enough available ports")

    return allocator


# def mount_site_volumes(site: Site) -> list:
#     volumes = site.rebased_volumes_upon_nua_conf()
#     create_docker_volumes(volumes)
#     mounted_volumes = []
#     for volume_params in volumes:
#         mounted_volumes.append(new_docker_mount(volume_params))
#     return mounted_volumes


def mount_resource_volumes(rsite: Resource) -> list:
    create_docker_volumes(rsite.volume)
    mounted_volumes = []
    for volume_params in rsite.volume:
        mounted_volumes.append(new_docker_mount(volume_params))
    return mounted_volumes


def extra_host_gateway() -> dict:
    """Sent an update for docker parameters 'extra_hosts':

    host.docker.internal.
    """
    return {"host.docker.internal": docker_host_gateway_ip()}


def unused_volumes(orig_mounted_volumes: list) -> list:
    current_mounted = store.list_instances_container_active_volumes()
    current_sources = {vol["source"] for vol in current_mounted}
    return [vol for vol in orig_mounted_volumes if vol["source"] not in current_sources]


def create_docker_volumes(volumes_config: list):
    for volume_params in volumes_config:
        docker_volume_create_or_use(volume_params)


def new_docker_mount(volume_params: dict) -> docker.types.Mount:
    volume = Volume.parse(volume_params)
    if volume.type == "volume":
        driver_config = new_docker_driver_config(volume)
    else:
        driver_config = None
    read_only = bool(volume.options.get("read_only", False))
    if volume.type == "tmpfs":
        tmpfs_size = size_to_bytes(volume.options.get("tmpfs_size")) or None
        tmpfs_mode = volume.options.get("tmpfs_mode") or None
    else:
        tmpfs_size, tmpfs_mode = None, None

    return docker.types.Mount(
        volume.target,
        volume.source or None,
        volume.type,
        driver_config=driver_config,
        read_only=read_only,
        tmpfs_size=tmpfs_size,
        tmpfs_mode=tmpfs_mode,
    )


def new_docker_driver_config(volume: Volume) -> docker.types.DriverConfig | None:
    """Volume driver configuration for Docker.

    Only valid for the 'volume' type.
    """
    if not volume.driver or volume.driver == "local":
        return None
    # to be completed
    return docker.types.DriverConfig(volume.driver)


def unmount_unused_volumes(orig_mounted_volumes: list):
    for unused in unused_volumes(orig_mounted_volumes):
        docker_volume_prune(unused)


def start_one_container(rsite: Resource, mounted_volumes: list):
    run_params = rsite.run_params
    if mounted_volumes:
        run_params["mounts"] = mounted_volumes
    rsite.run_params = run_params
    if verbosity(4):
        print(f"start_one_container() run_params:\n{pformat(run_params)}")
    secrets = secrets_dict(rsite.requested_secrets)
    new_container = docker_run(rsite, secrets)
    rsite.container_id = new_container.id
    if mounted_volumes:
        rsite.run_params["mounts"] = True
    if verbosity(1):
        info(f"    -> container of name: {rsite.container}")
        info(f"            container id: {rsite.container_id_short}")
        if rsite.network_name:
            info(f"    connected to network: {rsite.network_name}")


def stop_previous_containers(sites: list):
    pass


def deactivate_containers(container_names: list[str]):
    for name in container_names:
        if not name:
            continue
        docker_remove_container_previous(name)
        store.instance_delete_by_container(name)


def deactivate_site(site: Site):
    """Deactive containers of Site and all sub Resources (updating orchestrator
    DB)."""
    container_names = [res.container for res in site.resources]
    container_names.append(site.container)
    deactivate_containers(container_names)


def deactivate_all_instances():
    """Find all instances in DB.

    - remove container if it exists
    - remove site from DB
    """
    for instance in store.list_instances_all():
        if verbosity(2):
            print(
                f"Removing from containers and DB: "
                f"'{instance.app_id}' instance on '{instance.domain}'"
            )
        site_config = instance.site_config
        container_names = [
            res.get("container", "") for res in site_config.get("resources", [])
        ]
        container_names.append(site_config["container"])
        container_names = [name for name in container_names if name]
        deactivate_containers(container_names)

    docker_network_prune()


def start_container_engine():
    """Ensure the containr system is running.

    Currrently: only checking that Docker daemon is up.
    """
    docker_service_start_if_needed()


def create_container_private_network(network_name: str):
    """Create a private network for the container (and it's surb containers).

    Currrently: only managing Docker bridge network.
    """
    docker_network_create_bridge(network_name)


def pull_resource_container(resource: Resource) -> bool:
    """Retrieve a resource container.

    Currrently: only managing Docker bridge network.
    """
    if resource.type != "docker":
        warning(f"Unknown resource type: {resource.type}")
        return True
    if verbosity(1):
        info(f"Pulling image '{resource.image}'")
    docker_image = docker_require(resource.image)
    if not docker_image:
        warning(f"No image found for '{resource.image}'")
        return False
    if verbosity(1):
        display_one_docker_img(docker_image)
    resource.image_id = docker_image.id
    return True
