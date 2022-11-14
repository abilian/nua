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
    - install it locally an load the image in the local registry of the Nua
    orchestrator.
"""
import json
import tempfile
from contextlib import suppress
from pathlib import Path

import docker
import docker.errors
import requests
from fabric import Connection

from ..deep_access_dict import DeepAccessDict
from ..server_utils.mini_log import log_me


def name_tag(tagged_name: str) -> tuple:
    parts = tagged_name.split(":")
    if len(parts) == 1:
        return tagged_name, ""
    return "-".join(parts[:-1]), parts[-1]


def remove_exising_image(image_id: str):
    # if image already there, erase to replace by new version:
    client = docker.from_env()
    try:
        image = client.images.get(image_id)
        log_me(f"removing pre-existing: {image.id}")
    except docker.errors.ImageNotFound:
        # log_me(f"no existing image {image_id}")
        pass
    else:
        with suppress(docker.errors.APIError):
            client.images.remove(image_id, force=True, noprune=False)


def log_me_result(cmd: str, result) -> None:
    if not result:
        return
    if cmd and (result.stdout or result.stderr):
        log_me(f"{cmd}:")
    if result.stdout:
        for line in result.stdout.split("\n"):
            if line.strip():
                log_me(f"stdout: {line.strip()}")
    if result.stderr:
        for line in result.stderr.split("\n"):
            if line.strip():
                log_me(f"stderr: {line.strip()}")


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
        self.config = DeepAccessDict(config)
        self.reg_address = self.config.read("registry", "local", "address")
        self.reg_port = self.config.read("registry", "local", "host_port")
        self.connect = self.config.read("connection")
        self.allow_transport = set()
        self.allow_repository = set()
        container_types = self.config.read("container") or []
        for container in container_types:
            if container.get("format") != "docker":
                continue
            self.allow_transport.add(container.get("transport"))
            self.allow_repository.add(container.get("repository"))
        self.groups = set()  # not implemented
        # log_me(f"DockerCommand allow_repository {self.allow_repository}")
        # log_me(f"DockerCommand config {self.config}")

    def check_allowed_command(self, transport: str = "", repository: str = "") -> bool:
        if (transport and transport not in self.allow_transport) or (
            repository and repository not in self.allow_repository
        ):
            raise NotImplementedError(
                f"Command not available for this Nua orchestrator "
                f"configuration.rep:{repository} allow:{self.allow_repository}"
            )
        return True

    def list(self) -> list[str]:
        """List Nua packages in local repository."""
        log_me(f"DockerCommand.list allow_repository {self.allow_repository}")
        self.check_allowed_command(repository="registry")
        result = []
        for repos in self.registry_repositories():
            tags = self.registry_repo_tags(repos)
            for tag in tags:
                result.append(f"{repos}:{tag}")
        return result

    def run(self, destination: str, image_id: str) -> None:
        """Start installed package on remote host or group of hosts.

        name is also accepted for image_id. destination is
        "user@host:port"
        """
        self.check_allowed_command(transport="ssh")
        if destination in self.groups:
            log_me("docker_install: installation groups not implemented")
        log_me(f"docker_run: {destination} {image_id}")
        timeout = self.connect.get("connect_timeout") or 10
        kwargs = self.connect.get("connect_kwargs") or {}
        if "key_filename" in kwargs:
            path = Path(kwargs["key_filename"]).expanduser()
            kwargs["key_filename"] = str(path)
        with Connection(
            destination, connect_timeout=timeout, connect_kwargs=kwargs
        ) as cnx:
            cmd = f"docker run -d {image_id}"
            result = cnx.run(
                cmd,
                warn=True,
                hide=True,
            )
            log_me_result(cmd, result)

        return True

    def stop(self) -> str:
        """Stop running package on remote host or group of hosts."""
        raise NotImplementedError

    def deploy(self) -> str:
        """Install and run package from local repository to remote host or
        group of hosts."""
        raise NotImplementedError

    def install(self, destination: str, image_id: str) -> bool:
        """Install package from local repository to remote host or group of
        hosts.

        name is also accepted for image_id. destination is
        "user@host:port"
        """
        self.check_allowed_command(transport="ssh", repository="registry")
        if destination in self.groups:
            log_me("docker_install: installation groups not implemented")
        log_me(f"docker_install: {destination} {image_id}")
        timeout = self.connect.get("connect_timeout") or 10
        kwargs = self.connect.get("connect_kwargs") or {}
        if "key_filename" in kwargs:
            path = Path(kwargs["key_filename"]).expanduser()
            kwargs["key_filename"] = str(path)
        with tempfile.TemporaryDirectory(
            prefix="nua_inst_", dir="/var/tmp", ignore_cleanup_errors=True
        ) as tmpdirname:
            tmpdir = Path(tmpdirname)
            # log_me(f"docker_install: {tmpdir=}")
            client = docker.from_env()
            try:
                image = client.images.get(image_id)
            except docker.errors.APIError:
                image = None
            # log_me(f"docker_install: {image=}")
            if not image:
                log_me(f"docker_install: Image {image_id} not found")
                print(f"Image {image_id} not found.")
                return False
            # fixme: specify local registry or automatic ?
            # repos, tag = self.repos_tag(nua_tag) ?
            # seems to be automatic
            labels = image.attrs["Config"]["Labels"] or {}
            nua_tag = labels.get("NUA_TAG")
            # log_me(f"docker_install: {nua_tag=}")
            if not nua_tag:
                log_me(f"docker_install: No NUA_TAG found in image {image_id} labels")
                return False
            tarfile = tmpdir / f"{nua_tag}.tar"
            # log_me(f"docker_install: {tarfile=}")
            with open(tarfile, "wb") as output:
                for chunk in image.save():
                    output.write(chunk)
            with Connection(
                destination, connect_timeout=timeout, connect_kwargs=kwargs
            ) as cnx:
                cmd = "mkdir -p tmp/nua_inst"
                result = cnx.run(
                    cmd,
                    warn=True,
                    hide=True,
                )
                log_me_result(cmd, result)
                try:
                    result = cnx.put(tarfile, "tmp/nua_inst/")
                except Exception as e:
                    log_me(f"'put {tarfile} tmp/nua_inst/' did raise:")
                    log_me(e)
                    return False
                cmd = f"docker load -i tmp/nua_inst/{nua_tag}.tar"
                result = cnx.run(
                    cmd,
                    warn=True,
                    hide=True,
                )
                log_me_result(cmd, result)
                cmd = f"rm -f tmp/nua_inst/{nua_tag}.tar"
                result = cnx.run(
                    cmd,
                    warn=True,
                    hide=True,
                )
                log_me_result(cmd, result)

        return True

    def registry_repositories(self) -> list:
        url = f"http://{self.reg_address}:{self.reg_port}"
        try:
            response = requests.get(f"{url}/v2/_catalog?n=5000")
        except requests.ConnectionError:
            return []
        if response.status_code != 200:
            return []
        return sorted(json.loads(response.content).get("repositories")) or []

    def registry_repo_tags(self, repository: str) -> list:
        url = f"http://{self.reg_address}:{self.reg_port}"
        try:
            response = requests.get(f"{url}/v2/{repository}/tags/list")
        except requests.ConnectionError:
            return []
        if response.status_code != 200:
            return []
        return sorted(json.loads(response.content).get("tags")) or []

    def repos_tag(self, tagged_name: str) -> tuple:
        name, tag = name_tag(tagged_name)
        repos = f"{self.reg_address}:{self.reg_port}/{name}"
        return repos, tag

    def push(self, nua_tag: str, image_id: str) -> str:
        """Tag and push in local registry.

        name is also accepted for image_id.
        """
        self.check_allowed_command(repository="registry")
        # log_me("push")
        client = docker.from_env()
        try:
            image = client.images.get(image_id)
        except docker.errors.APIError:
            image = None
        if not image:
            log_me(f"docker_push: Image {image_id} not found")
            print(f"Image {image_id} not found.")
            return False

        repos, tag = self.repos_tag(nua_tag)
        image.tag(repos, tag=tag)
        result = client.api.push(repository=repos, tag=tag)
        return result

    def load(self, destination: str, image_id: str) -> str:
        """Tag and push in local registry from remote docker instance.

        name is also accepted for image_id. destination is
        "user@host:port"
        """
        self.check_allowed_command(transport="ssh", repository="registry")
        timeout = self.connect.get("connect_timeout") or 10
        kwargs = self.connect.get("connect_kwargs") or {}
        if "key_filename" in kwargs:
            path = Path(kwargs["key_filename"]).expanduser()
            kwargs["key_filename"] = str(path)
        # log_me(f"{kwargs=}")
        # S108 Probable insecure usage of temp file/directory.
        Path("/var/tmp/nua_rcv").mkdir(  # noqa: S108
            mode=0o755, parents=True, exist_ok=True
        )

        with Connection(
            destination, connect_timeout=timeout, connect_kwargs=kwargs
        ) as cnx:
            # log_me(f"run docker save for '{image_id}':")
            cnx.run(
                f"mkdir -p /var/tmp/nua_src && docker save {image_id} > /var/tmp/nua_src/image.tar"
            )
            # log_me(f"run get for '{image_id}':")
            cnx.get(
                remote="/var/tmp/nua_src/image.tar",  # noqa: S108
                local="/var/tmp/nua_rcv/image.tar",  # noqa: S108
            )
            # log_me("clean nua_src")
            cnx.run("rm -fr /var/tmp/nua_src")
            # log_me("end cnx")
        remove_exising_image(image_id)
        client = docker.from_env()
        images_before = {img.id for img in client.images.list()}
        # log_me(f"{images_before=}")
        with open("/var/tmp/nua_rcv/image.tar", "rb") as input:  # noqa: S108
            client.images.load(input)
        images_after = {img.id for img in client.images.list()}
        new = images_after - images_before
        if not new:
            log_me("Warning: apparently, no new image was added")
        Path("/var/tmp/nua_rcv/image.tar").unlink()  # noqa: S121, S108
        image = client.images.get(image_id)
        labels = image.attrs["Config"]["Labels"] or {}
        # log_me(image.attrs["Config"])
        nua_tag = labels.get("NUA_TAG")
        if not nua_tag:
            log_me(f"docker_load: No NUA_TAG found in image {image_id} labels")
            return
        self.push(nua_tag, image.id)
