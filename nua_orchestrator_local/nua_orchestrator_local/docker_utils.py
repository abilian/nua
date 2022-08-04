"""Docker scripting utils."""
from datetime import datetime
from functools import wraps
from subprocess import run  # noqa: S404

import docker

from . import config
from .panic import panic
from .rich_console import print_magenta, print_red


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
