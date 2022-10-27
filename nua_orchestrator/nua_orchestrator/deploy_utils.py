"""class to manage the deployment of a group os sites
"""
from pathlib import Path

# from pprint import pprint
from typing import Callable

import docker

from .archive_search import ArchiveSearch
from .db import store
from .docker_utils import (
    display_one_docker_img,
    docker_host_gateway_ip,
    docker_volume_create_or_use,
    docker_volume_prune,
)
from .rich_console import print_green, print_magenta, print_red
from .server_utils.net_utils import check_port_available
from .site import Site
from .state import verbosity
from .utils import size_to_bytes


def load_install_image(image_path: str | Path) -> tuple:
    """Install docker image (tar file) in local docker daeon.

    Return: tuple(image_id, image_nua_config)
    """
    path = Path(image_path)
    # image is local, so we can mount it directly
    if not path.is_file():
        raise FileNotFoundError(path)
    arch_search = ArchiveSearch(path)
    image_nua_config = arch_search.nua_config_dict()
    if not image_nua_config:
        print_red(f"Error: image non compatible Nua: {path}.")
        raise ValueError("No Nua config found")
    metadata = image_nua_config["metadata"]
    msg = "Installing App: {id} {version}, {title}".format(**metadata)
    print_magenta(msg)
    client = docker.from_env()
    # images_before = {img.id for img in client.images.list()}
    with open(path, "rb") as input:  # noqa: S108
        loaded = client.images.load(input)
    if not loaded or len(loaded) > 1:
        print_red("Warning: loaded image result is strange:")
        print_red(f"{loaded=}")
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
        raise RuntimeError("Not enough available port")

    return allocator


def mount_volumes(site: Site) -> list:
    volumes = site.rebased_volumes_upon_nua_conf()
    create_docker_volumes(volumes)
    mounted_volumes = []
    for volume_params in volumes:
        mounted_volumes.append(new_docker_mount(volume_params))
    return mounted_volumes


def add_host_gateway(run_params: dict):
    extra_hosts = run_params.get("extra_hosts", {})
    extra_hosts["host.docker.internal"] = docker_host_gateway_ip()
    run_params["extra_hosts"] = extra_hosts


def volume_print(volume: dict):
    lst = ["  "]
    lst.append("type={type}, ".format(**volume))
    if "driver" in volume:
        lst.append("driver={driver}, ".format(**volume))
    lst.append("source={source}, target={target}".format(**volume))
    if "-> domains" in volume:
        lst.append("\n  domains: " + ", ".join(volume["domains"]))
    print("".join(lst))


def unused_volumes(orig_mounted_volumes: list) -> list:
    current_mounted = store.list_instances_container_active_volumes()
    current_sources = {vol["source"] for vol in current_mounted}
    return [vol for vol in orig_mounted_volumes if vol["source"] not in current_sources]


def create_docker_volumes(volumes_config):
    for volume_params in volumes_config:
        docker_volume_create_or_use(volume_params)


def new_docker_mount(volume_params: dict) -> docker.types.Mount:
    tpe = volume_params.get("type", "volume")  # either "volume", "bind", "tmpfs""
    # Container path.
    target = volume_params.get("target") or volume_params.get("destination")
    # Mount source (e.g. a volume name or a host path).
    source = volume_params.get("source")  # for "volume" or "bind" types
    driver_config = new_docker_driver_config(volume_params) if tpe == "volume" else None
    read_only = bool(volume_params.get("read_only", False))
    if tpe == "tmpfs":
        tmpfs_size = size_to_bytes(volume_params.get("tmpfs_size")) or None
        tmpfs_mode = volume_params.get("tmpfs_mode") or None
    else:
        tmpfs_size, tmpfs_mode = None, None
    return docker.types.Mount(
        target,
        source,
        type=tpe,
        driver_config=driver_config,
        read_only=read_only,
        tmpfs_size=tmpfs_size,
        tmpfs_mode=tmpfs_mode,
    )


def new_docker_driver_config(volume_params: dict) -> docker.types.DriverConfig | None:
    """Volume driver configuration. Only valid for the 'volume' type."""
    driver = volume_params.get("driver")
    if not driver or driver == "local":
        return None
    # to be completed
    return docker.types.DriverConfig(driver)


def unmount_unused_volumes(orig_mounted_volumes: list):
    for unused in unused_volumes(orig_mounted_volumes):
        docker_volume_prune(unused)


def stop_previous_containers(sites: list):
    pass