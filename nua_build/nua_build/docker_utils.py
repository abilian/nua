"""Docker scripting utils."""
from datetime import datetime
from functools import wraps

import docker

from .panic import panic
from .rich_console import print_magenta, print_red


def print_log_stream(docker_log):
    for line in docker_log:
        if "stream" in line:
            print("    ", line["stream"].strip())


def docker_build_log_error(func):
    @wraps(func)
    def build_log_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except docker.errors.BuildError as e:
            print("=" * 60)
            print_red("Something went wrong with image build!")
            print_red(str(e))
            print("=" * 60)
            print_log_stream(e.build_log)
            panic("Exiting.")

    return build_log_wrapper


def display_docker_img(iname):
    print_magenta(f"Docker image for '{iname}':")
    client = docker.from_env()
    result = client.images.list(filters={"reference": iname})
    if not result:
        print("No image found")
        return
    for img in result:
        sid = img.short_id.split(":")[-1]
        tags = "|".join(img.tags)
        crea = datetime.fromisoformat(img.attrs["Created"][:19]).isoformat(" ")
        # Note on size of image: Docker uses 10**6 for MB, here I use 2**20
        size = round(img.attrs["Size"] / 2**20)
        print(f"    tags: {tags}")
        print(f"    id: {sid}")
        print(f"    size: {size}MB")
        print(f"    created: {crea}")
