import docker
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


register_methods(DockerCommand)
