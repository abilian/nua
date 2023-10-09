"""Docker scripting utils."""
import re
import string
from datetime import datetime
from functools import wraps

import docker
from docker import DockerClient
from docker.errors import APIError, BuildError, ImageNotFound
from docker.models.images import Image
from docker.utils.json_stream import json_stream

from nua.lib.panic import Abort, debug, important, print_stream, red_line, vprint
from nua.lib.tool.state import verbosity, verbosity_level

LOCAL_CONFIG = {"size_unit_MiB": False}
RE_SUCCESS = re.compile(r"(^Successfully built |sha256:)([0-9a-f]+)$")


# def vprint_log_stream(docker_log: list):
#     for line in docker_log:
#         if "stream" in line:
#             vprint("    ", line["stream"].strip())


def docker_build_log_error(func):
    @wraps(func)
    def build_log_error_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except BuildError as e:
            with verbosity(0):
                red_line("=" * 60)
                red_line("Something went wrong with image build!")
                red_line(str(e))
                red_line("=" * 60)
            raise Abort("Exiting.")

        except APIError as e:
            with verbosity(0):
                message = ["=" * 60]
                message.append("Something went wrong with image build!")
                if e.is_client_error():
                    message.append(f"{e.response.status_code} Client Error")
                elif e.is_server_error():
                    message.append(f"{e.response.status_code} Server Error")
                message.append(f"URL: {e.response.url}")
                message.append(f"Reason: {e.response.reason}")
                message.append(f"Explanation: {e.explanation}")
                message.append("=" * 60)
                for line in message:
                    red_line(line)
            raise Abort("Exiting.")

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


def docker_sanitized_name(name: str) -> str:
    """Docker valid name.

    https://docs.docker.com/engine/reference/commandline/
    tag/#extended-description
    """
    # first replace spaces per underscores
    content = "_".join(name.split())
    # then apply docjer rules
    allowed = set(string.ascii_lowercase + string.digits + ".-_")
    content = "".join([c for c in content.strip().lower() if c in allowed])
    while ("___") in content:
        content.replace("___", "__")
    for sep in ".-_":
        while content.startswith(sep):
            content = content[1:]
        while content.endswith(sep):
            content = content[:-1]
    content = content[:128]
    return content


def image_labels(reference: str) -> dict:
    image = docker_require(reference)
    if not image:
        return {}
    return image.labels


def display_docker_img(image_name: str):
    important(f"Container image for '{image_name}':")
    client = DockerClient.from_env()
    result = client.images.list(filters={"reference": image_name})
    if not result:
        red_line("No image found")
        return
    for img in result:
        display_one_docker_img(img)  # pyright: ignore


def display_one_docker_img(image: Image):
    sid = image.id.split(":")[-1][:10]  # pyright: ignore
    tags = "|".join(image.tags)
    crea = datetime.fromisoformat(image_created_as_iso(image)).isoformat(" ")
    # Note on size of image: Docker uses 10**6 for MB, not 2**20
    size = docker_image_size(image)
    vprint(f"    tags: {tags}")
    vprint(f"    id: {sid}")
    vprint(f"    size: {size}{size_unit()}")
    vprint(f"    created: {crea}")


def docker_require(reference: str) -> Image | None:
    return docker_get_locally(reference) or docker_pull(reference)


def docker_remove_locally(reference: str):
    client = DockerClient.from_env()
    try:
        image = client.images.get(reference)
        if image:
            with verbosity(3):
                debug(f"Image '{reference}' found in local Docker instance: remove it")
            client.images.remove(image=image.id, force=True, noprune=False)
    except (APIError, ImageNotFound):
        pass


def docker_get_locally(reference: str) -> Image | None:
    client = DockerClient.from_env()
    try:
        name = reference.split("/")[-1]
        image = client.images.get(name)
        if image:
            with verbosity(3):
                vprint(f"Image '{reference}' found in local Docker instance")
        return image  # pyright: ignore
    except (APIError, ImageNotFound):
        with verbosity(4):
            vprint(f"Image '{reference}' not found in local Docker instance")
        return None


def docker_pull(reference: str) -> Image | None:
    client = DockerClient.from_env()
    try:
        image = client.images.pull(reference)
        if image:
            with verbosity(3):
                vprint(f"Image '{reference}' pulled from Docker hub")
        return image  # pyright: ignore
    except (APIError, ImageNotFound):
        with verbosity(3):
            vprint(f"Image '{reference}' not found in Docker hub")
        return None


def _print_buffer_log(messages: list[str]):
    """Print messages buffered, without checking for verbosity.

    Dump retained messages when an error occured."""
    for message in messages:
        with verbosity(0):
            print_stream(message)


def _docker_stream_chunk(
    chunk: dict,
    messages_buffer: list[str],
    result: dict,
) -> None:
    if "error" in chunk:
        _print_buffer_log(messages_buffer)
        raise BuildError(chunk["error"], "")
    result["last_event"] = chunk
    message = chunk.get("stream")
    if message:
        if match := RE_SUCCESS.search(message):
            result["image_id"] = match.group(2)
        with verbosity(2):
            print_stream(message)
        if verbosity_level() < 2:
            # store message for printing full log if later an error occurs
            messages_buffer.append(message)


def docker_stream_build(
    path: str,
    tag: str,
    buildargs: dict,
    labels: dict,
) -> str:
    messages_buffer: list[str] = []
    client = docker.from_env()
    resp = client.api.build(
        path=path,
        tag=tag,
        rm=True,
        forcerm=True,
        buildargs=buildargs,
        labels=labels,
        nocache=True,
        timeout=1800,
    )
    stream = json_stream(resp)
    result: dict[str, str] = {}
    for chunk in stream:
        _docker_stream_chunk(chunk, messages_buffer, result)
    if "image_id" not in result:
        _print_buffer_log(messages_buffer)
        raise BuildError(result.get("last_event", "Unknown"), "")
    return result["image_id"]
