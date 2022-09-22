"""Docker scripting utils."""
import json
from datetime import datetime
from functools import cache, wraps
from pprint import pformat
from subprocess import run  # noqa: S404
from time import sleep

import docker

from . import config
from .db import store
from .db.model.instance import RUNNING
from .panic import panic
from .rich_console import print_magenta, print_red
from .state import verbosity

# from pprint import pprint


def print_log_stream(docker_log):
    for line in docker_log:
        if "stream" in line:
            print("    ", line["stream"].strip())


def docker_build_log_error(func):
    @wraps(func)
    def build_log_error_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except docker.errors.BuildError as e:
            print("=" * 60)
            print_red("Something went wrong with image build!")
            print_red(str(e))
            print("=" * 60)
            print_log_stream(e.build_log)
            panic("Exiting.")

    return build_log_error_wrapper


def image_created_as_iso(image):
    return image.attrs["Created"][:19]


def docker_image_size(image):
    return image_size_repr(round(image.attrs["Size"]))


def image_size_repr(image_bytes):
    if config.read("nua", "ui", "size_unit_MiB"):
        return round(image_bytes / 2**20)
    return round(image_bytes / 10**6)


def size_unit():
    return "MiB" if config.read("nua", "ui", "size_unit_MiB") else "MB"


def display_docker_img(iname):
    print_magenta(f"Docker image for '{iname}':")
    client = docker.from_env()
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


def display_one_docker_img(img):
    sid = img.id.split(":")[-1][:10]
    tags = "|".join(img.tags)
    crea = datetime.fromisoformat(image_created_as_iso(img)).isoformat(" ")
    # Note on size of image: Docker uses 10**6 for MB, here I use 2**20
    size = docker_image_size(img)
    print(f"    tags: {tags}")
    print(f"    id: {sid}")
    print(f"    size: {size}{size_unit()}")
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


def docker_list_container(name: str):
    client = docker.from_env()
    return client.containers.list(filters={"name": name})


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
    previous_name = store.instance_container(site["domain"], site["prefix"])
    if not previous_name:
        return
    if verbosity(1):
        print_magenta(f"    -> remove previous container: {previous_name}")
    docker_kill_container(previous_name)
    docker_remove_container(previous_name)
    if verbosity(3):
        containers = docker_list_container(previous_name)
        print("docker_remove_container after", containers)

    store.instance_delete_by_domain_prefix(site["domain"], site["prefix"])


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


def store_container_instance(site):
    meta = site["image_nua_config"]["metadata"]
    store.store_instance(
        app_id=meta["id"],
        nua_tag=store.nua_tag_string(meta),
        domain=site["domain"],
        prefix=site["prefix"],
        container=site["container"],
        image=site["image"],
        state=RUNNING,
        site_config=site,
    )


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
    client = docker.from_env()
    cont = client.containers.run(image_id, **params)
    if verbosity(3):
        name = params["name"]
        print("run done:", docker_list_container(name))
    if not docker_check_container_listed(cont.name):
        panic(f"Something failed when starting container {cont.name}")
    site["container"] = cont.name
    store_container_instance(site)
    if verbosity(1):
        print_magenta(f"    -> run new container         '{site['container']}'")


def docker_list_volume(name: str) -> list:
    client = docker.from_env()
    lst = client.volumes.list(filters={"name": name})
    # filter match is not equality
    return [vol for vol in lst if vol.name == name]


#  "/var/tmp" includes invalid characters for a local volume


def docker_create_volume(volume_opt: dict):
    driver = volume_opt.get("driver", "local")
    if driver != "local" and not install_plugin(driver):
        # assuming it is the name of a plugin
        print_red(f"Install of Docker's plugin '{driver}' failed.")
        panic("Exiting.")
    client = docker.from_env()
    # volume = client.volumes.create(
    client.volumes.create(
        name=volume_opt["source"],
        driver=driver,
        # driver's options, using format of python-docker:
        driver_opts=volume_opt.get("options", {}),
    )
    # return volume


def docker_volume_create_or_use(volume_opt: dict):
    """Return a useabla/mountable docker volume."""
    if volume_opt.get("type") == "bind":
        # no need to create "bind" volumes
        return
    found = docker_list_volume(volume_opt["source"])
    # if found:
    #     return found[0]
    # return docker_create_volume(volume_opt)
    if not found:
        docker_create_volume(volume_opt)


def install_plugin(plugin_name: str) -> str:
    client = docker.from_env()
    try:
        plugin = client.plugins.get(plugin_name)
    except docker.errors.NotFound:
        plugin = None
    if not plugin:
        try:
            plugin = client.plugins.install(plugin_name)
        except docker.errors.APIError:
            plugin = None
    if plugin:
        return plugin.name
    else:
        return ""
