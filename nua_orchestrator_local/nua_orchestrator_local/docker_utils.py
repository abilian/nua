"""Docker utils."""
import json
from datetime import datetime
from functools import cache, wraps
from pprint import pformat
from subprocess import run  # noqa: S404
from time import sleep

from docker import Container, DockerClient, Image, from_env
from docker.errors import APIError, BuildError, ImageNotFound, NotFound

from . import config
from .db import store

# from .db.model.instance import RUNNING
from .panic import error
from .rich_console import print_magenta, print_red
from .state import verbosity
from .utils import image_size_repr, size_unit


def print_log_stream(docker_log):
    for line in docker_log:
        if "stream" in line:
            print("    ", line["stream"].strip())


def docker_build_log_error(func):
    @wraps(func)
    def build_log_error_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BuildError as e:
            print("=" * 60)
            print_red("Something went wrong with image build!")
            print_red(str(e))
            print("=" * 60)
            print_log_stream(e.build_log)
            error("Build error.")

    return build_log_error_wrapper


def image_created_as_iso(image):
    return image.attrs["Created"][:19]


def docker_image_size(image):
    return image_size_repr(
        round(image.attrs["Size"]), config.read("nua", "ui", "size_unit_MiB")
    )


def display_docker_img(iname):
    print_magenta(f"Docker image for '{iname}':")
    client = from_env()
    result = client.images.list(filters={"reference": iname})
    if not result:
        print("No image found")
        return
    for img in result:
        display_one_docker_img(img)


@cache
def docker_host_gateway_ip() -> str:
    cmd = ["ip", "-j", "route"]
    completed = run(cmd, capture_output=True)  # noqa: S607, S603
    for route in json.loads(completed.stdout):
        if route.get("dev") == "docker0":
            return route.get("prefsrc", "")
    return ""


def display_one_docker_img(image: Image):
    sid = image.id.split(":")[-1][:10]
    tags = "|".join(image.tags)
    crea = datetime.fromisoformat(image_created_as_iso(image)).isoformat(" ")
    # Note on size of image: Docker uses 10**6 for MB, here I use 2**20
    size = docker_image_size(image)
    as_mib = config.read("nua", "ui", "size_unit_MiB")
    print(f"    tags: {tags}")
    print(f"    id: {sid}")
    print(f"    size: {size}{size_unit(as_mib)}")
    print(f"    created: {crea}")


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


def docker_list_container(name: str) -> list[Container]:
    client = from_env()
    return client.containers.list(filters={"name": name})


def docker_pull(image: str) -> Image:
    client = from_env()
    try:
        return client.images.pull(image)
    except (APIError, ImageNotFound) as e:
        print(f"Error while pulling image '{image}'")
        print(e)
        return None


def _docker_wait_empty_container_list(name: str, timeout: int) -> bool:
    if not timeout:
        timeout = 1
    count = timeout * 10
    while docker_list_container(name):
        if count <= 0:
            return False
        count -= 1
        sleep(0.1)
    return True


def docker_kill_container(name: str):
    if not name:
        return
    containers = docker_list_container(name)
    if verbosity(3):
        print("docker_kill_container", containers)
    if not containers:
        return
    for cont in containers:
        cont.kill()
    if not _docker_wait_empty_container_list(
        name, config.read("host", "docker_kill_timeout")
    ):
        for remain in docker_list_container(name):
            print_red(f"Warning: container not killed: {remain}")
    # if verbosity(3):
    #     containers = docker_list_container(name)
    #     print("docker_kill_container after", containers)


def _docker_remove_container(name: str, force=False):
    if force and verbosity(1):
        print_red(f"Warning: removing container with '--force': {name}")
    for cont in docker_list_container(name):
        cont.remove(v=True, force=force)


def _docker_display_not_removed(name: str):
    for remain in docker_list_container(name):
        print_red(f"Warning: container not removed: {remain}")


def docker_remove_container(name: str, force=False):
    if not name:
        return
    if verbosity(3):
        containers = docker_list_container(name)
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
    while not docker_list_container(name):
        if count <= 0:
            return False
        count -= 1
        sleep(0.1)
    return True


def docker_check_container_listed(name: str) -> bool:
    if _docker_wait_container_listed(name):
        return True
    else:
        print_red(f"Warning: container not seen in list: {name}")
        print_red("         container listed:")
        for cont in docker_list_container(name):
            print_red(f"         {cont.name}  {cont.status}")
        return False


def docker_remove_prior_container_db(site: dict):
    """Search & remove containers already configured for this same site
    (running or stopped), from DB."""
    previous_name = store.instance_container(site["domain"])
    if not previous_name:
        return
    if verbosity(1):
        print_magenta(f"    -> remove previous container: {previous_name}")
    docker_kill_container(previous_name)
    docker_remove_container(previous_name)
    if verbosity(3):
        containers = docker_list_container(previous_name)
        print("docker_remove_container after", containers)

    store.instance_delete_by_domain(site["domain"])


def docker_remove_container_db(domain: str):
    """Remove container of full domain name from running container and DB"""
    docker_kill_container(domain)
    docker_remove_container(domain)
    store.instance_delete_by_domain(domain)


def docker_remove_prior_container_live(site: dict):
    """Search & remove containers already configured for this same site
    (running or stopped), from Docker.

    Security feature: try to remove containers of exactly same name that
    could be found in docker daemon:
    """
    previous_name = site["run_params"]["name"]
    if not previous_name:
        return
    for cont in docker_list_container(previous_name):
        print_red(f"Try removing a container not listed in Nua DB: {cont.name}")
        docker_kill_container(cont.name)
        docker_remove_container(cont.name)


def _erase_previous_container(client: DockerClient, name: str):
    try:
        container = client.containers.get(name)
        print_red(f"    -> Remove existing container '{container.name}'")
        container.remove(force=True)
    except APIError:
        pass


def docker_run(site: dict):
    image_id = site["image_id"]
    params = site["run_params"]
    if verbosity(1):
        print_magenta(f"Docker run image '{image_id}'")
        if verbosity(2):
            print("run parameters:\n", pformat(params))
    docker_remove_prior_container_db(site)
    docker_remove_prior_container_live(site)
    params["detach"] = True  # force detach option
    client = from_env()
    _erase_previous_container(client, params["name"])
    cont = client.containers.run(image_id, **params)
    if verbosity(3):
        name = params["name"]
        print("run done:", docker_list_container(name))
    if not docker_check_container_listed(cont.name):
        error(f"Failed starting container {cont.name}")
    site["container"] = cont.name


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
