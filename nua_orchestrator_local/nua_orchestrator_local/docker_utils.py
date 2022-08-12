"""Docker scripting utils."""
from datetime import datetime
from functools import wraps
from subprocess import run  # noqa: S404

import docker

from . import config
from .db import store
from .db.model.instance import RUNNING
from .panic import panic
from .rich_console import print_magenta, print_red

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


def docker_kill_container(name: str):
    if not name:
        return
    containers = docker_list_container(name)
    if containers:
        for cont in containers:
            cont.kill()


def docker_remove_container(name: str):
    if not name:
        return
    containers = docker_list_container(name)
    if containers:
        for cont in containers:
            cont.remove()


def docker_remove_prior_container_db(site: dict):
    """Search & remove containers already configured for this same site
    (running or stopped), from DB."""
    container_name = store.instance_container(site["domain"], site["prefix"])
    if container_name:
        print_magenta(f"    -> remove previous container '{container_name}'")
        docker_kill_container(container_name)
        docker_remove_container(container_name)
        store.instance_delete_by_domain_prefix(site["domain"], site["prefix"])


def docker_remove_prior_container_live(site: dict):
    """Search & remove containers already configured for this same site
    (running or stopped), from Docker.

    Security feature: try to remove containers of exactly same name that
    could be found in docker daemon:
    """
    container_name = site["run_params"]["name"]
    if container_name:
        containers = docker_list_container(container_name)
        if containers:
            for cont in containers:
                cont.kill()
                cont.remove()
                print_magenta(f"    -> remove previous container '{container_name}'")


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
    print_magenta(f"Docker run image '{image_id}'")
    docker_remove_prior_container_db(site)
    docker_remove_prior_container_live(site)
    params["detach"] = True  # force detach option
    client = docker.from_env()
    cont = client.containers.run(image_id, **params)
    site["container"] = cont.name
    store_container_instance(site)
    print_magenta(f"    -> run new container         '{site['container']}'")


def docker_list_volume(name: str) -> list:
    client = docker.from_env()
    lst = client.volumes.list(filters={"name": name})
    # filter match is not equality
    return [vol for vol in lst if vol.name == name]


def docker_create_volume(volume_opt: dict):
    client = docker.from_env()
    volume = client.volumes.create(name=volume_opt["name"], driver=volume_opt["driver"])
    return volume


def docker_volume_create_or_use(volume_opt: dict):
    """Return a usable docker volume"""
    found = docker_list_volume(volume_opt["name"])
    if found:
        return found[0]
    return docker_create_volume(volume_opt)
