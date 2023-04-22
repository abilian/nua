"""Docker utils."""
import io
import json
import re
from contextlib import suppress
from copy import deepcopy
from functools import cache
from pathlib import Path
from pprint import pformat
from subprocess import run  # noqa: S404
from time import sleep

from docker import DockerClient
from docker.errors import APIError, NotFound
from docker.models.containers import Container
from docker.models.images import Image
from nua.autobuild.docker_build_utils import docker_require
from nua.lib.console import print_red
from nua.lib.panic import Abort, important, info, show, vprint, warning
from nua.lib.shell import chmod_r, mkdir_p
from nua.lib.tool.state import verbosity

from . import config
from .db import store
from .resource import Resource
from .volume import Volume

RE_VAR = re.compile(r"\{[^\{\}]+\}")


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


def docker_container_of_name(name: str) -> list[Container]:
    """Send a list of 0 or 1 Container of the given name."""
    client = DockerClient.from_env()
    try:
        return [
            cont
            for cont in client.containers.list(all=True, filters={"name": name})
            if cont.name == name
        ]
    except NotFound:
        return []


def docker_start_container_name(name: str):
    if not name:
        return
    containers = docker_container_of_name(name)
    with verbosity(3):
        vprint("docker_start_container_name():", containers)
    if not containers:
        warning(f"docker_start_container_name(): no container of name '{name}'")
        return
    for ctn in containers:
        _docker_start_container(ctn)


def docker_restart_container_name(name: str):
    if not name:
        return
    containers = docker_container_of_name(name)
    with verbosity(3):
        vprint("docker_restart_container_name():", containers)
    if not containers:
        warning(f"docker_restart_container_name(): no container of name '{name}'")
        return
    for ctn in containers:
        _docker_restart_container(ctn)


def _docker_wait_empty_container_list(name: str, timeout: int) -> bool:
    if not timeout:
        timeout = 1
    count = timeout * 10
    while docker_container_of_name(name):
        if count <= 0:
            return False
        count -= 1
        sleep(0.1)
    return True


def docker_stop_container_name(name: str):
    if not name:
        return
    containers = docker_container_of_name(name)
    with verbosity(3):
        vprint("docker_stop_container_name():", containers)
    if not containers:
        warning(f"docker_stop_container_name(): no container of name '{name}'")
        return
    for ctn in containers:
        _docker_stop_container(ctn)
    if not _docker_wait_empty_container_list(
        name, config.read("host", "docker_kill_timeout")
    ):
        pass
        # for remain in docker_container_of_name(name):
        #     warning(f"container not killed: {remain.name}")


def _docker_stop_container(container: Container):
    try:
        container.stop()
    except APIError as e:
        warning(f"Stopping container error: {e}")


def _docker_start_container(container: Container):
    try:
        container.start()
    except APIError as e:
        warning(f"Starting container error: {e}")


def _docker_restart_container(container: Container):
    try:
        container.restart()
    except APIError as e:
        warning(f"Restarting container error: {e}")


def _docker_remove_container(name: str, force=False, volume=False):
    if force and verbosity(1):
        warning(f"removing container with '--force': {name}")
    for cont in docker_container_of_name(name):
        cont.remove(v=volume, force=force)


def _docker_display_not_removed(name: str):
    for remain in docker_container_of_name(name):
        warning(f"container not removed: {remain}")


def docker_remove_container(name: str, force=False):
    if not name:
        return
    with verbosity(3):
        containers = docker_container_of_name(name)
        vprint("docker_remove_container", containers)
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
    while not docker_container_of_name(name):
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
        for cont in docker_container_of_name(name):
            print_red(f"         {cont.name}  {cont.status}")
        return False


def docker_remove_prior_container_db(rsite: Resource):
    """Search & remove containers already configured for this same AppInstance
    or Resource (running or stopped), from DB."""
    if rsite.type != "nua-site":
        # FIXME for resource containers
        return

    previous_name = store.instance_container(rsite.domain)
    if not previous_name:
        return

    with verbosity(1):
        info(f"    -> remove previous container: {previous_name}")

    docker_stop_container_name(previous_name)
    docker_remove_container(previous_name)

    with verbosity(4):
        containers = docker_container_of_name(previous_name)
        vprint("docker_remove_container after", containers)

    store.instance_delete_by_domain(rsite.domain)


def docker_remove_container_previous(name: str, show_warning: bool = True):
    """Remove container of full domain name from running container and DB."""
    containers = docker_container_of_name(name)
    with verbosity(4):
        vprint(f"Stopping container: {pformat(containers)}")

    if not containers:
        if show_warning:
            with verbosity(2):
                warning(f"no previous container to stop '{name}'")
        return

    container = containers[0]
    with verbosity(2):
        info(f"Stopping container '{container.name}'")
    _docker_stop_container(container)
    with verbosity(2):
        info(f"Removing container '{container.name}'")
    try:
        container.remove(v=False, force=True)
    except (NotFound, APIError):
        # container was "autoremoved" after stop
        pass


def docker_remove_prior_container_live(rsite: Resource):
    """Search & remove containers already configured for this same AppInstance
    or Resource (running or stopped), from Docker.

    Security feature: try to remove containers of exactly same name that
    could be found in docker daemon:
    """
    previous_name = rsite.run_params.get("name", "")
    if not previous_name:
        return

    for container in docker_container_of_name(previous_name):
        print_red(f"Try removing a container not listed in Nua DB: {container.name}")
        docker_stop_container_name(container.name)
        docker_remove_container(container.name)


def erase_previous_container(client: DockerClient, name: str):
    try:
        with verbosity(2):
            info(f"Search previous container of name: {name}")
        container = client.containers.get(name)
        info(f"    -> Remove existing container '{container.name}'")
        container.remove(force=True)
    except APIError:
        pass


def docker_run_params(rsite: Resource) -> dict:
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


def docker_run(rsite: Resource, secrets: dict) -> Container:
    """Wrapper on top of the py-docker run() command.

    Returns:
        The new started container.
    """
    params = docker_run_params(rsite)
    with verbosity(1):
        # info(f"Docker run image: {rsite.image_id}")
        info(f"Docker run image: {rsite.image}")
        info(f"        image id: {rsite.image_id_short}")
        with verbosity(2):
            important("Docker run parameters:")
            show(pformat(params))

    docker_remove_prior_container_live(rsite)
    with verbosity(2):
        if "network" in params:
            info("Network:", params["network"])

    container = _docker_run(rsite, secrets, params)
    with verbosity(3):
        vprint("Docker secrets:", secrets)

    _check_run_container(container, rsite.container_name)
    return container


def _docker_run(rsite: Resource, secrets: dict, params: dict) -> Container:
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


def docker_exec_stdout(container: Container, params: dict, output: io.BufferedWriter):
    """Wrapper on top of the py-docker exec_run() command, capturing the
    output.

    Defaults are:
    cmd, stdout=True, stderr=True, stdin=False, tty=False, privileged=False,
    user='', detach=False, stream=False, socket=False, environment=None,
    workdir=None, demux=False

    Returns:
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
        output.write(data[0])


def docker_exec(container: Container, params: dict):
    """Wrapper on top of the py-docker exec_run() command, without capturing
    the output.

    Defaults are:
    cmd, stdout=False, stderr=False, stdin=False, tty=False, privileged=False,
    user='', detach=False, stream=False, socket=False, environment=None,
    workdir=None, demux=False

    Returns:
    """
    cmd = params["cmd"]
    user = params.get("user", "")
    workdir = params.get("workdir")
    _, stream = container.exec_run(
        cmd=cmd,
        user=user,
        workdir=workdir,
        stream=False,
        stdout=False,
        stderr=False,
        demux=True,
    )


def test_docker_exec(container: Container):
    # path = Path(f"/var/tmp/test_{container.name}.txt")
    # print(f"test_docker_exec() for {path}")
    params = {"cmd": "find /nua"}
    try:
        # with open(path, "wb") as output:
        # docker_exec_stdout(container, params, output)
        docker_exec(container, params)
    except APIError as e:
        print(e)
        raise RuntimeError(f"Test of container failed:\ndocker logs {container.id}")


def docker_volume_list(name: str) -> list:
    client = DockerClient.from_env()
    lst = client.volumes.list(filters={"name": name})
    # filter match is not equality
    return [vol for vol in lst if vol.name == name]


def docker_remove_volume_by_source(source: str):
    for volume in docker_volume_list(source):
        try:
            volume.remove(force=True)
        except APIError as e:
            print(e)


def docker_volume_create(volume: Volume):
    found = docker_volume_list(volume.source)
    if not found:
        docker_volume_create_new(volume)


def docker_volume_create_new(volume: Volume):
    """Create a new volume of type "volume"."""
    if volume.driver != "local" and not install_plugin(volume.driver):
        # assuming it is the name of a plugin
        raise Abort(f"Install of Docker's plugin '{volume.driver}' failed.")

    client = DockerClient.from_env()
    client.volumes.create(
        name=volume.source,
        driver=volume.driver,
        # driver's options, using format of python-docker:
        driver_opts=volume.options,
    )


def docker_volume_create_local_dir(volume: Volume):
    """For volumes of type "bind", create a local directory on the host if
    needed.

    This my use more options in future versions.
    """
    if Path(volume.source).exists():
        return
    mkdir_p(volume.source)
    chmod_r(volume.source, 0o644, 0o755)


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

    The strategy depends on the volume type: "bind", "volume", or
    "tmpfs".
    """
    volume = Volume.parse(volume_params)
    if volume.type == "volume":
        return docker_volume_create(volume)
    if volume.type == "bind":
        return docker_volume_create_local_dir(volume)
    # for "tmpfs", volumes do not need to be created before
    # container loading


def docker_volume_prune(volume_opt: dict):
    """Remove a (previously mounted) local docker volume.

    Beware: deleting data !
    """
    volume = Volume.parse(volume_opt)
    if volume.type != "volume" or volume.driver != "local":
        # todo: later, manage bind volumes
        return
    name = volume.source
    try:
        client = DockerClient.from_env()
        lst = client.volumes.list(filters={"name": name})
        # beware: filter match is not equality
        found = [vol for vol in lst if vol.name == name]
        if found:
            # shoud be only one.
            docker_volume = found[0]
            docker_volume.remove(force=True)
    except APIError as e:
        print("Error while unmounting volume:")
        print(pformat(volume_opt))
        print(e)


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


def install_plugin(plugin_name: str) -> str:
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
