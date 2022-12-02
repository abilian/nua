"""Docker utils."""
import json
from copy import deepcopy
from datetime import datetime
from functools import cache, wraps
from pprint import pformat
from subprocess import run  # noqa: S404
from time import sleep

from docker import DockerClient, from_env
from docker.errors import APIError, BuildError, ImageNotFound, NotFound
from docker.models.containers import Container
from docker.models.images import Image

# from .db.model.instance import RUNNING
from nua.lib.panic import error, info, warning
from nua.lib.rich_console import print_magenta, print_red
from nua.lib.tool.state import verbosity
from nua.selfbuilder.docker_build_utils import docker_require

from . import config
from .db import store
from .resource import Resource
from .utils import image_size_repr, size_unit


@cache
def docker_host_gateway_ip() -> str:
    cmd = ["ip", "-j", "route"]
    completed = run(cmd, capture_output=True)  # noqa: S607, S603
    for route in json.loads(completed.stdout):
        if route.get("dev") == "docker0":
            return route.get("prefsrc", "")
    return ""


def docker_service_is_active() -> bool:
    cmd = ["sudo", "service", "docker", "status"]
    completed = run(cmd, capture_output=True)  # noqa: S607, S603
    return completed.stdout.find(b"Active: active (running)") >= 0


def docker_service_stop():
    run(["sudo", "service", "docker", "stop"])  # noqa: S607, S603


def docker_service_start():
    run(["sudo", "service", "docker", "start"])  # noqa: S607, S603


def docker_service_start_if_needed():
    if not docker_service_is_active():
        docker_service_start()


def docker_container_of_name(name: str) -> list[Container]:
    """Send a list of 0 or 1 Continer of the given name."""
    client = from_env()
    return [c for c in client.containers.list(filters={"name": name}) if c.name == name]


def _docker_wait_empty_container_list(name: str, timeout: int) -> bool:
    if not timeout:
        timeout = 1
    count = timeout * 10
    while docker_container_of_name(name):
        if count <= 0:
            return False
        count -= 1
        sleep(0.1)
    return True


def docker_stop_container_name(name: str):
    if not name:
        return
    containers = docker_container_of_name(name)
    if verbosity(3):
        print("docker_stop_container_name():", containers)
    if not containers:
        warning(f"docker_stop_container_name(): no container of name '{name}'")
        return
    for ctn in containers:
        _docker_stop_container(ctn)
    if not _docker_wait_empty_container_list(
        name, config.read("host", "docker_kill_timeout")
    ):
        for remain in docker_container_of_name(name):
            warning(f"container not killed: {remain.name}")


def docker_stop_container(name: str):
    if not name:
        return
    containers = docker_container_of_name(name)
    if verbosity(3):
        print("docker_stop_container_name():", containers)
    if not containers:
        warning(f"docker_stop_container_name(): no container of name '{name}'")
        return
    for ctn in containers:
        _docker_stop_container(ctn)
    if not _docker_wait_empty_container_list(
        name, config.read("host", "docker_kill_timeout")
    ):
        for remain in docker_container_of_name(name):
            warning(f"container not killed: {remain.name}")


def _docker_stop_container(container: Container):
    try:
        container.stop()
    except APIError as e:
        warning(f"Stopping container error: {e}")


def _docker_remove_container(name: str, force=False, volume=False):
    if force and verbosity(1):
        warning(f"removing container with '--force': {name}")
    for cont in docker_container_of_name(name):
        cont.remove(v=volume, force=force)


def _docker_display_not_removed(name: str):
    for remain in docker_container_of_name(name):
        warning(f"container not removed: {remain}")


def docker_remove_container(name: str, force=False):
    if not name:
        return
    if verbosity(3):
        containers = docker_container_of_name(name)
        print("docker_remove_container", containers)
    _docker_remove_container(name, force=force)
    if _docker_wait_empty_container_list(
        name, config.read("host", "docker_remove_timeout")
    ):
        return
    _docker_display_not_removed(name)
    if not force:
        docker_remove_container(name, force=True)


def _docker_wait_container_listed(name: str) -> bool:
    timeout = config.read("host", "docker_run_timeout") or 5
    count = timeout * 10
    while not docker_container_of_name(name):
        if count <= 0:
            return False
        count -= 1
        sleep(0.1)
    return True


def docker_check_container_listed(name: str) -> bool:
    if _docker_wait_container_listed(name):
        return True
    else:
        warning(f"container not seen in list: {name}", "container listed:")
        for cont in docker_container_of_name(name):
            print_red(f"         {cont.name}  {cont.status}")
        return False


def docker_remove_prior_container_db(rsite: Resource):
    """Search & remove containers already configured for this same Site or
    Resource (running or stopped), from DB."""
    if rsite.type != "nua-site":
        # FIXME for resourc containers
        return
    previous_name = store.instance_container(rsite.domain)
    if not previous_name:
        return
    if verbosity(1):
        info(f"    -> remove previous container: {previous_name}")
    docker_stop_container_name(previous_name)
    docker_remove_container(previous_name)
    if verbosity(3):
        containers = docker_container_of_name(previous_name)
        print("docker_remove_container after", containers)
    store.instance_delete_by_domain(rsite.domain)


def docker_remove_container_previous(name: str):
    """Remove container of full domain name from running container and DB."""
    containers = docker_container_of_name(name)
    if verbosity(3):
        print(f"Stopping container: {pformat(containers)}")
    if containers:
        container = containers[0]
        if verbosity(2):
            print(f"Stopping container '{container.name}'")
        _docker_stop_container(container)
        if verbosity(2):
            print(f"Removing container '{container.name}'")
        try:
            container.remove(v=False, force=True)
        except NotFound:
            # container was "autoremoved" after stop
            pass
    else:
        warning(f"while removing container: no container of name '{name}'")


def docker_remove_prior_container_live(rsite: Resource):
    """Search & remove containers already configured for this same Site or
    Resource (running or stopped), from Docker.

    Security feature: try to remove containers of exactly same name that
    could be found in docker daemon:
    """
    previous_name = rsite.run_params.get("name", "")
    if not previous_name:
        return
    for container in docker_container_of_name(previous_name):
        print_red(f"Try removing a container not listed in Nua DB: {container.name}")
        docker_stop_container_name(container.name)
        docker_remove_container(container.name)


def _erase_previous_container(client: DockerClient, name: str):
    try:
        container = client.containers.get(name)
        info(f"    -> Remove existing container '{container.name}'")
        container.remove(force=True)
    except APIError:
        pass


def params_with_secrets(params: dict, secrets: dict):
    result = deepcopy(params)
    env = result.get("environment", {})
    env.update(secrets)
    result["environment"] = env
    return result


def docker_run(rsite: Resource, secrets: dict) -> Container:
    params = deepcopy(rsite.run_params)
    # the actual key is 'environment'
    if "env" in params:
        del params["env"]
    if verbosity(1):
        info(f"Docker run image: {rsite.image_id}")
        if verbosity(2):
            print("run parameters:\n", pformat(params))
    docker_remove_prior_container_live(rsite)
    params["detach"] = True  # force detach option
    if rsite.network_name:
        params["network"] = rsite.network_name
        if verbosity(2) and rsite.network_name:
            info("network:", rsite.network_name)
    client = from_env()
    _erase_previous_container(client, params["name"])
    actual_params = params_with_secrets(params, secrets)
    container = client.containers.run(rsite.image_id, **actual_params)
    if verbosity(3):
        name = params["name"]
        print("run done:", docker_container_of_name(name))
    if not docker_check_container_listed(container.name):
        error(f"Failed starting container {container.name}")
    rsite.container = container.name
    return container


def docker_volume_list(name: str) -> list:
    client = from_env()
    lst = client.volumes.list(filters={"name": name})
    # filter match is not equality
    return [vol for vol in lst if vol.name == name]


def docker_volume_create(volume_opt: dict):
    found = docker_volume_list(volume_opt["source"])
    if not found:
        docker_volume_create_new(volume_opt)


def docker_volume_create_new(volume_opt: dict):
    """Create a new volume of type "volume"."""
    driver = volume_opt.get("driver", "local")
    if driver != "local" and not install_plugin(driver):
        # assuming it is the name of a plugin
        error(f"Install of Docker's plugin '{driver}' failed.")
    client = from_env()
    client.volumes.create(
        name=volume_opt["source"],
        driver=driver,
        # driver's options, using format of python-docker:
        driver_opts=volume_opt.get("options", {}),
    )


# def docker_tmpfs_create(volume_opt: dict):
#     """Create a new volume of type "tmpfs"."""
#
#     client = from_env()
#     client.volumes.create(
#         name=volume_opt["source"],
#         driver=driver,
#         # driver's options, using format of python-docker:
#         driver_opts=volume_opt.get("options", {}),
#     )


def docker_volume_create_or_use(volume_opt: dict):
    """Return a useabla/mountable docker volume.

    Strategy depends of volume type: "bind", "volume", or "tmpfs".
    """
    if volume_opt.get("type") == "volume":
        docker_volume_create(volume_opt)
    else:
        # for "bind" or "tmpfs", volumes do not need to be created before
        # container loading
        pass


def docker_volume_prune(volume_opt: dict):
    """Remove a (previously mounted) local docker volume.

    Beware: deleting data !
    """
    if volume_opt.get("type") != "volume" or volume_opt.get("driver") != "local":
        # todo: later, manage bind volumes
        return
    name = volume_opt["source"]
    try:
        client = from_env()
        lst = client.volumes.list(filters={"name": name})
        # filter match is not equality
        found = [vol for vol in lst if vol.name == name]
        if found:
            # shoud be only one.
            volume = found[0]
            volume.remove(force=True)
    except APIError as e:
        print("Error while unmounting volume:")
        print("volume_opt")
        print(e)


def docker_network_create_bridge(network_name: str):
    client = from_env()
    found = docker_network_by_name(network_name)
    if found:
        return found
    else:
        return client.networks.create(network_name, driver="bridge")


def docker_network_prune():
    """prune all unused networks (no option in py-docker?)"""
    client = from_env()
    client.networks.prune()


def docker_network_by_name(network_name: str):
    client = from_env()
    all_nets = {netw.name: netw for netw in client.networks.list()}
    return all_nets.get(network_name)


def install_plugin(plugin_name: str) -> str:
    client = from_env()
    try:
        plugin = client.plugins.get(plugin_name)
    except NotFound:
        plugin = None
    if not plugin:
        try:
            plugin = client.plugins.install(plugin_name)
        except APIError:
            plugin = None
    if plugin:
        return plugin.name
    else:
        return ""


def pull_docker_image(image: str) -> Image:
    docker_service_start_if_needed()
    return docker_require(image)


def list_containers():
    client = from_env()
    for ctn in client.containers.list(all=True):
        image = ctn.image
        if image.tags:
            name = image.tags[0]
        else:
            name = image.short_id
        print(
            f"{ctn.name}\n"
            f"    status: {ctn.status}  id: {ctn.short_id}  image: {name}"
        )
