"""Docker scripting utils."""
from datetime import datetime
from functools import wraps

from docker import from_env
from docker.errors import APIError, BuildError, ImageNotFound
from docker.models.images import Image
from nua.lib.console import print_magenta, print_red
from nua.lib.panic import abort
from nua.lib.tool.state import verbosity

LOCAL_CONFIG = {"size_unit_MiB": False}


def print_log_stream(docker_log: list):
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
            abort("Exiting.")

    return build_log_error_wrapper


def image_created_as_iso(image):
    return image.attrs["Created"][:19]


def docker_image_size(image):
    return image_size_repr(round(image.attrs["Size"]))


def image_size_repr(image_bytes):
    if LOCAL_CONFIG.get("size_unit_MiB"):
        return round(image_bytes / 2**20)
    return round(image_bytes / 10**6)


def size_unit():
    return "MiB" if LOCAL_CONFIG.get("size_unit_MiB") else "MB"


def display_docker_img(iname: str):
    print_magenta(f"Docker image for '{iname}':")
    client = from_env()
    result = client.images.list(filters={"reference": iname})
    if not result:
        print("No image found")
        return
    for img in result:
        display_one_docker_img(img)


def display_one_docker_img(image: Image):
    sid = image.id.split(":")[-1][:10]
    tags = "|".join(image.tags)
    crea = datetime.fromisoformat(image_created_as_iso(image)).isoformat(" ")
    # Note on size of image: Docker uses 10**6 for MB, not 2**20
    size = docker_image_size(image)
    print(f"    tags: {tags}")
    print(f"    id: {sid}")
    print(f"    size: {size}{size_unit()}")
    print(f"    created: {crea}")


def docker_require(reference: str) -> Image | None:
    return docker_get_locally(reference) or docker_pull(reference)


def docker_remove_locally(reference: str):
    client = from_env()
    try:
        image = client.images.get(reference)
        if image and verbosity(3):
            print(f"Image '{reference}' found in local Docker instance: remove it")
            client.images.remove(image=image.id, force=True, noprune=False)
    except (APIError, ImageNotFound):
        pass


def docker_get_locally(reference: str) -> Image | None:
    client = from_env()
    try:
        name = reference.split("/")[-1]
        image = client.images.get(name)
        if image and verbosity(3):
            print(f"Image '{reference}' found in local Docker instance")
        return image
    except (APIError, ImageNotFound):
        if verbosity(4):
            print(f"Image '{reference}' not found in local Docker instance")
        return None


def docker_pull(reference: str) -> Image | None:
    client = from_env()
    try:
        image = client.images.pull(reference)
        if image and verbosity(3):
            print(f"Image '{reference}' pulled from Docker hub")
        return image
    except (APIError, ImageNotFound):
        if verbosity(3):
            print(f"Image '{reference}' not found in Docker hub")
        return None
