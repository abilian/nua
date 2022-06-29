"""Nua orchestrator docker commands.

Principle for fetching a new built package:
 - the Nua orchestrator host is considered as secure
 - the remote development host (running nua_build) is less secure
 - the connection is established from the Nua orch. host (assumin its public
   key is set on the development host)
 - the 'rload' commands:
    - connects to development host
    - "docker save" the image
    - fetch the image .tar file
    - install it loclly an load the image in the local registry of the Nua
    orchestrator.
"""
import docker
from fabric import Connection
from tinyrpc.dispatch import public

from ..rpc_utils import register_methods, rpc_trace


def name_tag(tagged_name: str) -> tuple:
    parts = tagged_name.split(":")
    if len(parts) == 1:
        return tagged_name, ""
    return "-".join(parts[:-1]), parts[-1]


def repos_tag(tagged_name: str) -> tuple:
    name, tag = name_tag(tagged_name)
    address = config.read("nua", "registry", "local", address)
    port = config.read("nua", "registry", "local", host_port)
    repos = f"{address}:{port}/{name}"
    return repos, tag


# [registry.local]
#     container.tag = "registry:2.8"
#     container.name = "nua-registry"
#     address = "127.0.0.1"
#     cont_port = "5000"
#     host_port = "5010"
#     volume.path = "/var/tmp/nua/registry/data"
#     volume.env = "REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY"
class DockerCommand:
    prefix = "docker_"

    def __init__(self, config: dict):
        self.config = config

    @rpc_trace
    def tag(self, nua_tag: str, image: docker.Image) -> bool:
        """Tag image.

        name is also accepted for image_id.
        """
        base_tag = ""
        for tag in image.tags:
            if tag.lower().startswith("nua"):
                base_tag = tag
                break
        if not base_tag:
            print(f"Image {image_id} is not a Nua build.")
            return False
        name, tag = name_tag(nua_tag)
        address = config.read("nua", "registry", "local", address)
        port = config.read("nua", "registry", "local", host_port)
        repos = f"{address}:{port}/{name}"
        return image.tag(rpos, tag=tag)

    @public
    @rpc_trace
    def push(self, nua_tag: str, image_id: str) -> str:
        """Tag and push in local registry.

        name is also accepted for image_id.
        """
        client = docker.from_env()
        try:
            image = client.images.get(image_id)
        except docker.errors.APIError:
            image = None
        if not image:
            print(f"Image {image_id} not found.")
            return False
        self.tag(image, nua_tag)
        repos, tag = repos_tag(nua_tag)
        result = client.api.push(repository=repos, tag=tag)
        return result

    @public
    @rpc_trace
    def rload(self, remote: str, nua_tag: str, image_id: str) -> str:
        """Tag and push in local registry from remote docker instance.

        name is also accepted for image_id.
        remote is "user@host"
        """
        with Connection("jd@localhost") as cnx:
            try:
                cnx.run(f"docker save {image_id} > /var/tmp/image.tar")
                cnx.get(
                    remote_path="/var/tmp/image.tar", local_path="/var/tmp/image.tar"
                )
            except Exception:
                raise
        image = client.images.load("/var/tmp/image.tar")
        return self.push(nua_tag, image.id)


register_methods(DockerCommand)
