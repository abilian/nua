"""Docker utils."""
import io
import json
import re
import shlex
from contextlib import suppress
from copy import deepcopy
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from pprint import pformat
from subprocess import run  # noqa: S404
from subprocess import PIPE, STDOUT, Popen
from time import sleep
from typing import Any

from docker import DockerClient
from docker.errors import APIError, ImageNotFound, NotFound
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.volumes import Volume as DockerVolume
from nua.lib.console import print_red
from nua.lib.docker import docker_require
from nua.lib.elapsed import elapsed
from nua.lib.panic import (
    Abort,
    bold_debug,
    debug,
    important,
    info,
    show,
    vprint,
    warning,
)
from nua.lib.shell import chmod_r, mkdir_p
from nua.lib.tool.state import verbosity

from . import config
from .provider import Provider
from .volume import Volume

RE_VAR = re.compile(r"\{[^\{\}]+\}")


# local daemon ######################################################


@cache
def docker_host_gateway_ip() -> str:
    cmd = ["ip", "-j", "route"]
    completed = run(cmd, capture_output=True)  # noqa: S607, S603
    for route in json.loads(completed.stdout):
        if route.get("dev") == "docker0":
            return route.get("prefsrc", "")
    return ""


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


# container #########################################################


def docker_container_of_name(
    name: str,
    client: DockerClient | None = None,
) -> Container | None:
    """Return the Container of the given name or None if not found."""
    if client is None:
        actual_client = DockerClient.from_env()
    else:
        actual_client = client
    try:
        return [
            cont
            for cont in actual_client.containers.list(all=True, filters={"name": name})
            if cont.name == name
        ][0]
    except (NotFound, IndexError):
        return None


# container action ##################################################


def _docker_container_mounts(container: Container) -> list[dict]:
    return container.attrs["Mounts"]


def docker_mount_point(container: Container, volume_name: str) -> str:
    for record in _docker_container_mounts(container):
        if record["Name"] == volume_name:
            return record["Destination"]
    return ""


def docker_container_volumes(container_name: str) -> list[DockerVolume]:
    volumes = []
    client = DockerClient.from_env()
    container = docker_container_of_name(container_name, client)
    if container is None:
        return volumes
    for mounted in _docker_container_mounts(container):
        volume = docker_volume_of_name(mounted["Name"], client)
        if volume is not None:
            volumes.append(volume)
    return volumes


def docker_container_named_volume(
    container_name: str,
    volume_name: str,
) -> DockerVolume | None:
    for volume in docker_container_volumes(container_name):
        if volume.attrs["Name"] == volume_name:
            return volume
    return None


def docker_container_status(container_id: str) -> str:
    """Get container status per Id."""
    client = DockerClient.from_env()
    try:
        cont = client.containers.get(container_id)
    except (NotFound, APIError):
        return "App is down: container not found (probably removed)"
    return (
        f"Container ID: {cont.short_id}, status: {cont.status}, "
        f"created: {elapsed(docker_container_since(cont))} ago"
    )


def docker_container_status_record(container_id: str) -> dict[str, Any]:
    """Return container status dict (per container Id)."""
    client = DockerClient.from_env()
    try:
        cont = client.containers.get(container_id)
    except (NotFound, APIError):
        return {"error": "App is down: container not found (probably removed)"}
    return {
        "id": cont.short_id,
        "status": cont.status,
        "created": f"{elapsed(docker_container_since(cont))} ago",
    }


def docker_container_status_raw(container: Container) -> tuple[str, int]:
    return container.status, docker_container_since(container)


def docker_container_since(container: Container) -> int:
    created = datetime.fromisoformat(container.attrs["Created"][:19])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return int((now - created).total_seconds())


def docker_start_container_name(name: str) -> bool:
    if not name:
        return False
    container = docker_container_of_name(name)
    if container is None:
        warning(f"docker_start_container_name(): no container of name '{name}'")
        return False
    with verbosity(3):
        vprint("docker_start_container_name():", container)
    return _docker_start_container(container)


def docker_restart_container_name(name: str):
    if not name:
        return
    container = docker_container_of_name(name)
    if container is None:
        warning(f"docker_restart_container_name(): no container of name '{name}'")
        return
    with verbosity(3):
        vprint("docker_restart_container_name():", container)
    _docker_restart_container(container)


def _docker_wait_empty_container_list(name: str, timeout: int) -> bool:
    if not timeout:
        timeout = 1
    count = timeout * 10
    while docker_container_of_name(name) is not None:
        if count <= 0:
            return False
        count -= 1
        sleep(0.1)
    return True


def docker_stop_container_name(name: str):
    if not name:
        return
    container = docker_container_of_name(name)
    if container is None:
        warning(f"docker_stop_container_name(): no container of name '{name}'")
        return
    with verbosity(3):
        vprint("docker_stop_container_name():", container)
    _docker_stop_container(container)
    if not _docker_wait_empty_container_list(
        name, config.read("host", "docker_kill_timeout")
    ):
        pass
        # for remain in docker_container_of_name(name):
        #     warning(f"container not killed: {remain.name}")


def docker_pause_container_name(name: str):
    if not name:
        return
    container = docker_container_of_name(name)
    if container is None:
        warning(f"docker_pause_container_name(): no container of name '{name}'")
        return
    with verbosity(3):
        vprint("docker_pause_container_name():", container)
    _docker_pause_container(container)


def docker_unpause_container_name(name: str):
    if not name:
        return
    container = docker_container_of_name(name)
    if container is None:
        warning(f"docker_unpause_container_name(): no container of name '{name}'")
        return
    with verbosity(3):
        vprint("docker_unpause_container_name():", container)
    _docker_unpause_container(container)


def _docker_stop_container(container: Container):
    try:
        container.stop()
    except APIError as e:
        warning(f"Stopping container error: {e}")


def _docker_pause_container(container: Container):
    try:
        container.pause()
    except APIError as e:
        warning(f"Pausing container error: {e}")


def _docker_unpause_container(container: Container):
    try:
        container.unpause()
    except APIError as e:
        warning(f"Unpausing container error: {e}")


def _docker_start_container(container: Container) -> bool:
    try:
        container.start()
        return True
    except APIError as e:
        warning(f"Starting container error: {e}")
        return False


def _docker_restart_container(container: Container):
    try:
        container.restart()
    except APIError as e:
        warning(f"Restarting container error: {e}")


def _docker_remove_container(name: str, force: bool = False, volume: bool = False):
    if force:
        with verbosity(0):
            warning(f"removing container with '--force': {name}")
    container = docker_container_of_name(name)
    if container is not None:
        container.remove(v=volume, force=force)


def _docker_display_not_removed(name: str):
    container = docker_container_of_name(name)
    if container is not None:
        warning(f"container not removed: {container}")


def docker_remove_container(name: str, force=False):
    if not name:
        return
    with verbosity(3):
        container = docker_container_of_name(name)
        vprint("docker_remove_container", container)
    _docker_remove_container(name, force=force)
    if _docker_wait_empty_container_list(
        name, config.read("host", "docker_remove_timeout")
    ):
        return
    _docker_display_not_removed(name)
    if not force:
        docker_remove_container(name, force=True)


def _docker_wait_container_listed(name: str) -> bool:
    timeout = config.read("host", "docker_run_timeout") or 30
    count = timeout * 10
    while docker_container_of_name(name) is None:
        if count <= 0:
            return False
        count -= 1
        sleep(0.1)
    return True


def docker_check_container_listed(name: str) -> bool:
    if _docker_wait_container_listed(name):
        return True
    else:
        warning(f"container not seen in running list: {name}", "container listed:")
        container = docker_container_of_name(name)
        if container is not None:
            print_red(f"         {container.name}  {container.status}")
        return False


def docker_remove_container_previous(name: str, show_warning: bool = True):
    """Remove container of full domain name from running container and DB."""
    container = docker_container_of_name(name)
    with verbosity(4):
        vprint(f"Stopping container: {container}")

    if container is None:
        if show_warning:
            with verbosity(1):
                warning(f"no previous container to stop '{name}'")
        return

    with verbosity(1):
        info(f"Stopping container '{container.name}'")
    _docker_stop_container(container)
    with verbosity(1):
        info(f"Removing container '{container.name}'")
    try:
        container.remove(v=False, force=True)
    except (NotFound, APIError):
        # container was "autoremoved" after stop
        pass


def docker_remove_prior_container_live(rsite: Provider):
    """Search & remove containers already configured for this same AppInstance
    or Provider (running or stopped), from Docker.

    Security feature: try to remove containers of exactly same name that
    could be found in docker daemon:
    """
    previous_name = rsite.run_params.get("name", "")
    if not previous_name:
        return

    container = docker_container_of_name(previous_name)
    if container is None:
        return
    with verbosity(3):
        debug(
            f"For security, try to remove a container not listed in Nua DB: {container.name}"
        )
    docker_stop_container_name(container.name)
    docker_remove_container(container.name)


def erase_previous_container(client: DockerClient, name: str):
    try:
        with verbosity(4):
            bold_debug(f"Search previous container of name: {name}")
        container = client.containers.get(name)
        info(f"    -> Remove existing container '{container.name}'")
        container.remove(force=True)
    except APIError:
        pass


def docker_run_params(rsite: Provider) -> dict:
    """Return the actual docker parameters."""
    params = deepcopy(rsite.run_params)
    # the actual key is 'environment'
    if "env" in params:
        del params["env"]
    params["detach"] = True  # force detach option
    if rsite.network_name:
        params["network"] = rsite.network_name
    if params.get("network", "") == "host":
        # remove all ports NAT
        with suppress(KeyError):
            del params["ports"]
    return params


def docker_run(rsite: Provider, secrets: dict) -> Container:
    """Wrapper on top of the py-docker run() command.

    Returns:
        The new started container.
    """
    params = docker_run_params(rsite)
    with verbosity(0):
        # info(f"Docker run image: {rsite.image_id}")
        info(f"Docker run image: {rsite.image}")
        info(f"        image id: {rsite.image_id_short}")
        with verbosity(2):
            important("Docker run parameters:")
            show(pformat(params))

    docker_remove_prior_container_live(rsite)
    with verbosity(1):
        if "network" in params:
            info("Network:", params["network"])

    container = _docker_run(rsite, secrets, params)
    with verbosity(3):
        vprint("Docker secrets:", secrets)

    _check_run_container(container, rsite.container_name)
    return container


def _docker_run(rsite: Provider, secrets: dict, params: dict) -> Container:
    client = DockerClient.from_env()
    erase_previous_container(client, params["name"])
    actual_params = params_with_secrets_and_f_strings(params, secrets)
    return client.containers.run(rsite.image_id, **actual_params)


def params_with_secrets_and_f_strings(params: dict, secrets: dict) -> dict:
    """Complete the docker run() environment parameter with secrets."""
    result = deepcopy(params)
    env = result.get("environment", {})
    env.update(secrets)
    fill_env_strings(env)
    result["environment"] = env
    return result


def fill_env_strings(env: dict):
    templates = {
        key: val
        for key, val in env.items()
        if isinstance(val, str) and RE_VAR.search(val)
    }
    if not templates:
        return
    values = deepcopy(env)
    recursion = 20
    while recursion:
        recursion -= 1
        filled = {}
        for key, val in templates.items():
            filled[key] = val.format(**values)
        values.update(filled)
        templates = {key: val for key, val in filled.items() if RE_VAR.search(val)}
        if not templates:
            env.update(values)
            return
    raise RuntimeError("Recursion limit when filling ENV variables")


def _check_run_container(container: Container, name: str):
    if not docker_check_container_listed(container.name):
        raise Abort(f"Failed starting container {container.name}")

    if name != container.name:
        warning("rsite.container_name != container.name")
        warning(f"rsite.container_name = {name}")
        warning(f"container.name = {container.name}")
    # test_docker_exec(container)


def docker_exec_stdout(container: Container, params: dict, output: io.BufferedIOBase):
    """Wrapper on top of the py-docker exec_run() command, capturing the
    output.

    Defaults are:
    cmd, stdout=True, stderr=True, stdin=False, tty=False, privileged=False,
    user='', detach=False, stream=False, socket=False, environment=None,
    workdir=None, demux=False

    Returns: None
    """
    cmd = params["cmd"]
    user = params.get("user", "")
    workdir = params.get("workdir")
    _, stream = container.exec_run(
        cmd=cmd,
        user=user,
        workdir=workdir,
        stream=True,
        stdout=True,
        stderr=False,
        demux=True,
    )
    for data in stream:
        print(data)
        output.write(data[0])


def docker_exec_no_output(container: Container, command: str):
    """Wrapper on top of the py-docker exec_run() command, not
    capturing the output.

    Defaults are:
    cmd, stdout=True, stderr=True, stdin=False, tty=False, privileged=False,
    user='', detach=False, stream=False, socket=False, environment=None,
    workdir=None, demux=False

    Returns: None
    """
    _, stream = container.exec_run(
        cmd=command,
        user="root",
        workdir="/",
        stream=True,
        stdout=True,
        stderr=False,
        demux=True,
    )
    for data in stream:
        print(data[0].decode())


def docker_exec_stdin(container: Container, cmd: str, input_file: Path) -> str:
    """Wrapper on top of the py-docker exec_run() command, capturing file to stdin.

    Defaults are:
    cmd, stdout=True, stderr=True, stdin=False, tty=False, privileged=False,
    user='', detach=False, stream=False, socket=False, environment=None,
    workdir=None, demux=False
    """
    docker_cmd = shlex.split(f"/usr/bin/docker exec -i {container.id} {cmd}")
    with open(input_file, "rb") as rfile:
        proc = Popen(
            docker_cmd,
            stdin=rfile,
            stdout=PIPE,
            stderr=STDOUT,
        )
        result, _ = proc.communicate()
    return result.decode("utf8")


def docker_exec_checked(container: Container, params: dict, output: io.BufferedIOBase):
    """Wrapper on top of the py-docker exec_run() command, capturing the
    output.

    Write the binary output of run_exec to output buffered io, or raise Runtime Error.

    Defaults are:
    cmd, stdout=True, stderr=True, stdin=False, tty=False, privileged=False,
    user='', detach=False, stream=False, socket=False, environment=None,
    workdir=None, demux=False

    Returns: None
    """
    cmd = params["cmd"]
    shcmd = f'sh -c "{cmd}"'
    user = params.get("user", "root")
    workdir = params.get("workdir", "/")
    stderr = params.get("stderr", True)
    _, stream = container.exec_run(
        cmd=shcmd,
        user=user,
        workdir=workdir,
        stream=True,
        stdout=True,
        stderr=stderr,
        demux=False,
    )
    # will test the first line only:
    test_passed = False
    for data in stream:
        if not test_passed:
            if b"OCI runtime exec failed" in data:
                raise RuntimeError(data.decode("utf8"))
            test_passed = True
        output.write(data)


def docker_exec_commands(container: Container, commands: list[str]):
    for command in commands:
        print("Command:", command)
        docker_exec_no_output(container, command)


# def docker_exec(container: Container, params: dict):
#     """Wrapper on top of the py-docker exec_run() command, without capturing
#     the output.

#     Defaults are:
#     cmd, stdout=False, stderr=False, stdin=False, tty=False, privileged=False,
#     user='', detach=False, stream=False, socket=False, environment=None,
#     workdir=None, demux=False

#     Returns:
#        None or raise (APIError)
#     """
#     cmd = params["cmd"]
#     user = params.get("user", "root")
#     workdir = params.get("workdir", "/")
#     _, stream = container.exec_run(
#         cmd=cmd,
#         user=user,
#         workdir=workdir,
#         stream=False,
#         stdout=False,
#         stderr=False,
#         demux=True,
#     )


# def test_docker_exec(container: Container):
#     # path = Path(f"/var/tmp/test_{container.name}.txt")
#     # print(f"test_docker_exec() for {path}")
#     params = {"cmd": "find /nua"}
#     try:
#         # with open(path, "wb") as output:
#         # docker_exec_stdout(container, params, output)
#         docker_exec(container, params)
#     except APIError as e:
#         print(e)
#         raise RuntimeError(f"Test of container failed:\ndocker logs {container.id}")

# Volumes ###########################################################


def docker_volume_of_name(
    name: str,
    client: DockerClient | None = None,
) -> DockerVolume | None:
    """Return the DockerVolume of the given name or None if not found."""
    if client is None:
        actual_client = DockerClient.from_env()
    else:
        actual_client = client
    try:
        return actual_client.volumes.get(name)
    except (NotFound, APIError):
        return None


def docker_volume_type(volume: Volume) -> str:
    if volume.is_managed:
        return "volume"
    elif volume.type == "directory":
        return "bind"
    return "tmpfs"


def docker_volume_list(name: str) -> list[DockerVolume]:
    client = DockerClient.from_env()
    pre_list = client.volumes.list(filters={"name": name})
    # filter match is not equality
    return [vol for vol in pre_list if vol.name == name]


def docker_remove_volume_by_source(source: str):
    for volume in docker_volume_list(source):
        try:
            volume.remove(force=True)
        except APIError as e:
            print(e)


def docker_volume_create(volume: Volume):
    found = docker_volume_list(volume.full_name)
    if not found:
        docker_volume_create_new(volume)


def docker_volume_create_new(volume: Volume):
    """Create a new volume of type "managed"."""
    if volume.driver in {"docker", "local"}:
        driver = "local"
    else:
        driver = volume.driver

    if driver != "local" and not install_plugin(driver):
        # assuming it is the name of a plugin
        raise Abort(f"Install of Docker's plugin '{driver}' failed.")
    client = DockerClient.from_env()
    client.volumes.create(
        name=volume.full_name,
        driver=driver,
        # driver's options, using format of python-docker:
        driver_opts=volume.options,
    )


def docker_volume_create_local_dir(volume: Volume):
    """For volumes of type "directory", create a local directory on the host if
    needed.

    May use more options.
    """
    path = volume.full_name
    if Path(path).exists():
        return
    mkdir_p(path)
    chmod_r(path, 0o644, 0o755)


# def docker_tmpfs_create(volume_opt: dict):
#     """Create a new volume of type "tmpfs"."""
#
#     client = DockerClient.from_env()
#     client.volumes.create(
#         name=volume_opt["source"],
#         driver=driver,
#         # driver's options, using format of python-docker:
#         driver_opts=volume_opt.get("options", {}),
#     )


def docker_volume_create_or_use(volume_params: dict):
    """Return an useable/mountable docker volume.

    The strategy depends on the volume type: "managed", "directory", or
    "tmpfs".
    """
    volume = Volume.parse(volume_params)
    if volume.is_managed:
        return docker_volume_create(volume)
    if volume.type == "directory":
        return docker_volume_create_local_dir(volume)
    # for "tmpfs", volumes do not need to be created before
    # container loading


def docker_volume_prune(volume_opt: dict):
    """Remove a (previously mounted) local docker volume.

    Beware: deleting data !
    """
    volume = Volume.parse(volume_opt)
    if not volume.is_managed or volume.driver not in {"docker", "local"}:
        # maybe later manage directory volumes
        return
    name = volume.full_name
    try:
        client = DockerClient.from_env()
        pre_list = client.volumes.list(filters={"name": name})
        # beware: filter match is not equality
        found = [vol for vol in pre_list if vol.name == name]
        if found:
            # shoud be only one.
            docker_volume = found[0]
            docker_volume.remove(force=True)
    except APIError as e:
        print("Error while unmounting volume:")
        print(pformat(volume_opt))
        print(e)


# network ###########################################################


def docker_network_create_bridge(network_name: str):
    client = DockerClient.from_env()
    found = docker_network_by_name(network_name)
    if found:
        return found
    else:
        return client.networks.create(network_name, driver="bridge")


def docker_network_remove_one(network_name: str):
    """Prune a network identified by its name."""
    network = docker_network_by_name(network_name)
    if network:
        try:
            network.remove()
        except APIError as e:
            print(e)


def docker_network_prune():
    """Prune all unused networks."""
    client = DockerClient.from_env()
    client.networks.prune()


def docker_network_by_name(network_name: str):
    """Return a network identified by its name."""
    client = DockerClient.from_env()
    for net in client.networks.list():
        if net.name == network_name:
            return net
    return None


def docker_wait_for_status(
    container: Container,
    expected: str = "running",
    timeout: int = 60,
) -> bool:
    while True:
        status, since = docker_container_status_raw(container)
        if status == expected:
            return True
        if status == "exited":
            print("Container did exit")
            return False
        if since > timeout:
            print(f"Timeout while waiting for container '{expected}' status")
            return False
        sleep(0.2)


def install_plugin(plugin_name: str) -> str:
    """Install Docker's plugin (plugin for API of remote services)."""
    client = DockerClient.from_env()
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


def pull_docker_image(image: str) -> Image:
    docker_service_start_if_needed()
    return docker_require(image)


def list_containers():
    client = DockerClient.from_env()
    for ctn in client.containers.list(all=True):
        image = ctn.image
        if image.tags:
            name = image.tags[0]
        else:
            name = image.short_id
        print(
            f"{ctn.name}\n"
            f"    status: {ctn.status}  id: {ctn.short_id}  image: {name}"
        )


def local_nua_images() -> list[Image]:
    client = DockerClient.from_env()
    try:
        images = [image for image in client.images.list() if "NUA_TAG" in image.labels]
    except (APIError, ImageNotFound):
        images = []
    return images
