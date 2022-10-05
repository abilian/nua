"""Nua main scripts.

Rem: maybe need to refactor the "site" thing into a class and refactor a lot
"""
from copy import deepcopy
from pathlib import Path
from pprint import pformat

# from pprint import pprint
from string import ascii_letters, digits

import docker
import tomli

from .. import config
from ..archive_search import ArchiveSearch
from ..certbot import protocol_prefix, register_certbot_domains
from ..db import store
from ..db.model.instance import RUNNING
from ..docker_utils import (
    display_one_docker_img,
    docker_host_gateway_ip,
    docker_remove_container_db,
    docker_run,
    docker_service_start_if_needed,
    docker_volume_create_or_use,
    docker_volume_prune,
)
from ..domain_split import DomainSplit
from ..nginx_util import (
    chown_r_nua_nginx,
    clean_nua_nginx_default_site,
    configure_nginx_hostname,
    nginx_restart,
)
from ..panic import error
from ..postgres import pg_check_listening, pg_restart_service, pg_run_environment
from ..rich_console import print_green, print_magenta, print_red
from ..search_cmd import search_nua
from ..server_utils.net_utils import check_port_available
from ..state import verbosity
from ..utils import size_to_bytes
from ..volume_utils import volumes_merge_config

ALLOW_DOCKER_NAME = set(ascii_letters + digits + "-_.")
# parameters passed as a dict to docker run
RUN_BASE = {
    "auto_remove": True,
    "extra_hosts": {"host.docker.internal": "host-gateway"},
}
RUN_DEFAULT = {
    "mem_limit": "8G",
    "container_port": 80,
}
# someservices in nua_config may nbe spelled in different ways:
SERVICES_ALIASES = {"postgresql": "postgres"}
SERVICE_RESTART = {"postgres": pg_restart_service}
SERVICE_ENVIRONMENT = {"postgres": pg_run_environment}


def deploy_nua(app_name: str) -> int:
    """Search, install and launch Nua image.

    (from local registry for now.)"""
    # if app_name.endswith(".toml") and Path(app_name).is_file():
    #     return deploy_nua_sites(app_name)
    if verbosity(2):
        print_magenta(f"image: '{app_name}'")
    results = search_nua(app_name)
    if not results:
        error(f"No image found for '{app_name}'.")
    # ensure docker is running
    docker_service_start_if_needed()
    # images are sorted by version, take the last one:
    image_id, image_nua_config = install_image(results[-1])
    deploy_image(image_id, image_nua_config)
    return 0


def install_image(image_path: str | Path) -> tuple:
    """Install docker image (tar file) in local docker daeon.

    Return: tuple(image_id, image_nua_config)
    """
    path = Path(image_path)
    # image is local, so we can mount it directly
    if not path.is_file():
        raise FileNotFoundError(path)
    arch_search = ArchiveSearch(path)
    image_nua_config = arch_search.nua_config_dict()
    if not image_nua_config:
        print_red(f"Error: image non compatible Nua: {path}.")
        raise ValueError("No Nua config found")
    metadata = image_nua_config["metadata"]
    msg = "Installing App: {id} {version}, {title}".format(**metadata)
    print_magenta(msg)
    client = docker.from_env()
    # images_before = {img.id for img in client.images.list()}
    with open(path, "rb") as input:  # noqa: S108
        loaded = client.images.load(input)
    if not loaded or len(loaded) > 1:
        print_red("Warning: loaded image result is strange:")
        print_red(f"{loaded=}")
    loaded_img = loaded[0]
    # images_after = {img.id for img in client.images.list()}
    # new = images_after - images_before
    if verbosity(1):
        print_green("Intalled image:")
        display_one_docker_img(loaded_img)
    return loaded_img.id, image_nua_config


def deploy_image(image_id: str, image_nua_config: dict):
    # here will used core functions of the orchestrator
    # - see if image is already deployed
    # - see if image got specific deploy configuration
    # - build specifc config for nginx and others
    # - build docker run command
    # - finally execute docker command
    print("No implemented")
    pass


def _configured_ports(site_list):
    used = set()
    for site in site_list:
        port = site.get("port")
        if not port:
            continue
        if port != "auto":
            used.add(int(port))
    return used


def _free_port(start_ports: int, end_ports: int, used: set) -> int:
    for port in range(start_ports, end_ports):
        if port not in used and check_port_available("127.0.0.1", str(port)):
            return port
    raise RuntimeError("Not enough available port")


def generate_ports(host_list: list):
    start_ports = config.read("nua", "ports", "start") or 8100
    end_ports = config.read("nua", "ports", "end") or 9000
    if verbosity(3):
        print(f"generate_ports() from {start_ports} to {end_ports}")
    # all sites from all hosts:
    site_list = [site for host in host_list for site in host["sites"]]
    used = _configured_ports(site_list)
    # list of ports used for domains / sites, trying to keep them unchanged
    used_domain_ports = store.ports_instances_domains()
    # print(f"{used_domain_ports=}")
    for port in used_domain_ports:
        used.add(port)
    if verbosity(3):
        print(f"used ports:\n {used}")
    for site in site_list:
        _generate_port(site, start_ports, end_ports, used)


def _generate_port(site, start_ports, end_ports, used):
    port = site.get("port")
    if not port:
        return
    if port == "auto":
        # current_instance_port = store.instance_port(site["domain"])
        # if current_instance_port:
        #     new_port = current_instance_port
        # else:
        new_port = _free_port(start_ports, end_ports, used)
        used.add(new_port)
        site["actual_port"] = new_port
    else:
        site["actual_port"] = port


def install_images(sites: list):
    # ensure docker is running
    docker_service_start_if_needed()
    installed = {}
    for site in sites:
        image_str = site["image"]
        results = search_nua(image_str)
        if not results:
            error(f"No image found for '{image_str}'. Exiting.")
        img_path = results[-1]  # results are sorted by version, take higher
        if img_path in installed:
            image_id = installed[img_path][0]
            image_nua_config = deepcopy(installed[img_path][1])
        else:
            image_id, image_nua_config = install_image(img_path)
            installed[img_path] = (image_id, image_nua_config)
        site["image_id"] = image_id
        site["image_nua_config"] = image_nua_config


def find_all_images(deploy_sites: dict) -> bool:
    images_found = set()
    for site in deploy_sites["site"]:
        image_str = site["image"]
        if image_str in images_found:
            continue
        results = search_nua(image_str)
        if not results:
            print_red(f"No image found for '{image_str}'.")
            return False
        images_found.add(image_str)
        if verbosity(1):
            print_red(f"image found: '{image_str}'.")
    return True


def create_docker_volumes(volumes_config):
    for volume_params in volumes_config:
        docker_volume_create_or_use(volume_params)


def new_docker_driver_config(volume_params: dict) -> docker.types.DriverConfig | None:
    """Volume driver configuration. Only valid for the 'volume' type."""
    driver = volume_params.get("driver")
    if not driver or driver == "local":
        return None
    # to be completed
    return docker.types.DriverConfig(driver)


def new_docker_mount(volume_params: dict) -> docker.types.Mount:
    tpe = volume_params.get("type", "volume")  # either "volume", "bind", "tmpfs""
    # Container path.
    target = volume_params.get("target") or volume_params.get("destination")
    # Mount source (e.g. a volume name or a host path).
    source = volume_params.get("source")  # for "volume" or "bind" types
    driver_config = new_docker_driver_config(volume_params) if tpe == "volume" else None
    read_only = bool(volume_params.get("read_only", False))
    if tpe == "tmpfs":
        tmpfs_size = size_to_bytes(volume_params.get("tmpfs_size")) or None
        tmpfs_mode = volume_params.get("tmpfs_mode") or None
    else:
        tmpfs_size, tmpfs_mode = None, None
    return docker.types.Mount(
        target,
        source,
        type=tpe,
        driver_config=driver_config,
        read_only=read_only,
        tmpfs_size=tmpfs_size,
        tmpfs_mode=tmpfs_mode,
    )


def mount_volumes(site: dict):
    volumes = volumes_merge_config(site)
    create_docker_volumes(volumes)
    mounted_volumes = []
    for volume_params in volumes:
        mounted_volumes.append(new_docker_mount(volume_params))
    return mounted_volumes


def nua_long_name(meta: dict) -> str:
    release = meta.get("release", "")
    rel_tag = f"-{release}" if release else ""
    nua_prefix = "" if meta["id"].startswith("nua-") else "nua-"
    return f"{nua_prefix}{meta['id']}-{meta['version']}{rel_tag}"


def add_host_gateway(run_params: dict):
    extra_hosts = run_params.get("extra_hosts", {})
    extra_hosts["host.docker.internal"] = docker_host_gateway_ip()
    run_params["extra_hosts"] = extra_hosts


def _run_parameters_container_name(site: dict) -> str:
    image_nua_config = site["image_nua_config"]
    meta = image_nua_config["metadata"]
    suffix = DomainSplit(site["domain"]).containner_suffix()
    app_name = nua_long_name(meta)
    name_base = f"{app_name}-{suffix}"
    return "".join([x for x in name_base if x in ALLOW_DOCKER_NAME])


def _run_parameters_container_ports(site: dict, run_params: dict) -> dict:
    if "container_port" in run_params:
        container_port = run_params["container_port"]
        del run_params["container_port"]
    else:
        container_port = 80
    host_port = site.get("actual_port")
    if host_port:
        ports = {f"{container_port}/tcp": host_port}
    else:
        ports = {}  # for app not using web interface (ie: computation storage only...)
    return ports


def _services_environment(site: dict) -> dict:
    run_env = {}
    for service in _required_services(site):
        if service in SERVICE_ENVIRONMENT:
            gen_environ_function = SERVICE_ENVIRONMENT[service]
            # function may need or not site param:
            run_env.update(gen_environ_function(site))
    return run_env


def _run_parameters_container_environment(site: dict) -> dict:
    image_nua_config = site["image_nua_config"]
    run_env = image_nua_config.get("run_env", {})
    run_env.update(_services_environment(site))
    run_env.update(site.get("run_env", {}))
    return run_env


def generate_container_run_parameters(site):
    """Return suitable parameters for the docker.run() command."""
    image_nua_config = site["image_nua_config"]
    run_params = deepcopy(RUN_BASE)
    run_params.update(image_nua_config.get("run", RUN_DEFAULT))
    add_host_gateway(run_params)
    run_params["name"] = _run_parameters_container_name(site)
    run_params["ports"] = _run_parameters_container_ports(site, run_params)
    run_params["environment"] = _run_parameters_container_environment(site)
    return run_params


def start_containers(sites: list):
    for site in sites:
        run_params = generate_container_run_parameters(site)
        # volumes need to be mounted before beeing passed as arguments to
        # docker.run()
        mounted_volumes = mount_volumes(site)
        if mounted_volumes:
            run_params["mounts"] = mounted_volumes
        site["run_params"] = run_params
        docker_run(site)
        if mounted_volumes:
            site["run_params"]["mounts"] = True
        store_container_instance(site)
        if verbosity(1):
            print_magenta(f"    -> run new container         '{site['container']}'")


def store_container_instance(site):
    meta = site["image_nua_config"]["metadata"]
    store.store_instance(
        app_id=meta["id"],
        nua_tag=store.nua_tag_string(meta),
        domain=site["domain"],
        container=site["container"],
        image=site["image"],
        state=RUNNING,
        site_config=site,
    )


def unused_volumes(orig_mounted_volumes: list) -> list:
    current_mounted = store.list_instances_container_active_volumes()
    current_sources = {vol["source"] for vol in current_mounted}
    return [vol for vol in orig_mounted_volumes if vol["source"] not in current_sources]


def unmount_unused_volumes(orig_mounted_volumes: list):
    for unused in unused_volumes(orig_mounted_volumes):
        docker_volume_prune(unused)


def display_used_volumes():
    if not verbosity(1):
        return
    current_mounted = store.list_instances_container_active_volumes()
    if not current_mounted:
        return
    print_green("Volumes used by current Nua configuration:")
    for volume in current_mounted:
        volume_print(volume)


def display_unused_volumes(orig_mounted_volumes: list):
    if not verbosity(1):
        return
    unused = unused_volumes(orig_mounted_volumes)
    if not unused:
        return
    print_green("Some volumes are mounted but not used by current Nua configuration:")
    for volume in unused:
        volume_print(volume)


def volume_print(volume: dict):
    lst = ["  "]
    lst.append("type={type}, ".format(**volume))
    if "driver" in volume:
        lst.append("driver={driver}, ".format(**volume))
    lst.append("source={source}, target={target}".format(**volume))
    if "-> domains" in volume:
        lst.append("\n  domains: " + ", ".join(volume["domains"]))
    print("".join(lst))


def deactivate_all_sites():
    """Find all instance in DB
    - remove container if exists
    - remove site from DB
    """
    instances = store.list_instances_all()
    for instance in instances:
        if verbosity(2):
            print(
                f"Removing from containers and DB: "
                f"'{instance.app_id}' instance on '{instance.domain}'"
            )
        docker_remove_container_db(instance.domain)


def stop_previous_containers(sites: list):
    pass


def _sites_per_host(deploy_sites: dict) -> dict:
    """Return a dict of sites per host.

    key : hostname (full name)
    value : list of web sites of hostname

    input format: dict contains a list of sites

    [[site]]
    domain = "test.example.com/instance1"
    image = "flask-one:1.2-1"
    [[site]]
    domain = "sloop.example.com"
    image = "nua-flask-upload-one:1.0-1"
    port = "auto"

    ouput format: dict of hostnames, with explicit port = "auto".

    {'sloop.example.com': [{'domain': 'sloop.example.com',
                          'image': 'nua-flask-upload-one:1.0-1',
                          'port': 'auto',
                          }],
    'test.example.com': [{'domain': 'test.example.com/instance1',
                         'image': 'flask-one:1.2-1',
                         'port': 'auto',
                         },
                         ...
    """
    domains = {}
    for site in deploy_sites["site"]:
        if "port" not in site:
            site["port"] = "auto"
        dom = DomainSplit(site.get("domain", ""))
        site["domain"] = dom.full_path()
        if dom.hostname not in domains:
            domains[dom.hostname] = []
        domains[dom.hostname].append(site)
    return domains


def _make_host_list(domains: dict) -> list:
    """Convert dict(hostname:[sites,..]) to list({hostname, sites}).

    ouput format:
    [{'hostname': 'test.example.com',
     'sites': [{'domain': 'test.example.com/instance1',
                 'image': 'flask-one:1.2-1',
                 'port': 'auto',
                 },
                {'domain': 'test.example.com/instance2',
                 'image': 'flask-one:1.2-1',
                 'port': 'auto',
                 },
                 ...
     {'hostname': 'sloop.example.com',
      'sites': [{'domain': 'sloop.example.com',
                 'image': 'nua-flask-upload-one:1.0-1',
                 'port': 'auto'}]}]
    """
    return [
        {"hostname": hostname, "sites": sites_list}
        for hostname, sites_list in domains.items()
    ]


def _classify_located_sites(host_list: list):
    """Return sites classified for location use.

    If not located, check it is the only one of the domain."""
    for host in host_list:
        sites_list = host["sites"]
        first = sites_list[0]  # by construction, there is at least 1 element
        dom = DomainSplit(first["domain"])
        if dom.location:
            _verify_located(host)
        else:
            _verify_not_located(host)


def _verify_located(host: dict):
    """host format:
     {'hostname': 'test.example.com',
      'sites': [{'domain': 'test.example.com/instance1',
                  'image': 'flask-one:1.2-1',
                  'port': 'auto',
                  },
                 {'domain': 'test.example.com/instance2',
                  'image': 'flask-one:1.2-1',
                  ...
    changed to:
    {'hostname': 'test.example.com',
     'located': True,
     'sites': [{'domain': 'test.example.com/instance1',
                 'image': 'flask-one:1.2-1',
                 'port': 'auto',
                 'location': 'instance1'
                 },
                {'domain': 'test.example.com/instance2',
                 'image': 'flask-one:1.2-1',
                 ...
    """
    known_location = set()
    valid = []
    hostname = host["hostname"]
    for site in host["sites"]:
        dom = DomainSplit(site["domain"])
        if not dom.location:
            image = site.get("image")
            port = site.get("port")
            print_red("Error: required location is missing, site discarded:")
            print_red(f"    for {hostname=} / {image=} / {port=}")
            continue
        if dom.location in known_location:
            image = site.get("image")
            port = site.get("port")
            print_red("Error: location is already used for a domain, site discarded:")
            print_red(f"    {hostname=} / {image=} / {port=}")
            continue
        known_location.add(dom.location)
        site["location"] = dom.location
        valid.append(site)
    host["sites"] = valid
    host["located"] = True


def _verify_not_located(host: dict):
    """host format:
        {'hostname': 'sloop.example.com',
         'sites': [{'domain': 'sloop.example.com',
                    'image': 'nua-flask-upload-one:1.0-1',
                    'port': 'auto'}]}]
    changed to:
        {'hostname': 'sloop.example.com',
         'located': False,
         'sites': [{'domain': 'sloop.example.com',
                    'image': 'nua-flask-upload-one:1.0-1',
                    'port': 'auto'}]}]
    """
    # we know that the first of the list is not located. We expect the list
    # has only one site.
    if len(host["sites"]) == 1:
        valid = host["sites"]
    else:
        hostname = host["hostname"]
        valid = []
        valid.append(host["sites"].pop(0))
        print_red(f"Error: too many sites for {hostname=}, site discarded:")
        for site in host["sites"]:
            image = site.get("image")
            port = site.get("port")
            print_red(f"    {image=} / {port=}")
    host["sites"] = valid
    host["located"] = False


def sort_per_host(deploy_sites: dict) -> list:
    host_list = _make_host_list(_sites_per_host(deploy_sites))
    _classify_located_sites(host_list)
    return host_list


def host_list_to_sites(host_list: list) -> list:
    """Convert to list of sites format.

    output format:
    [{'actual_port': 8100,
      'hostname': 'test.example.com',
      'domain': 'test.example.com/instance1',
      'location': 'instance1',
      'image': 'flask-one:1.2-1',
      'port': 'auto'},
     {'actual_port': 8101,
      'hostname': 'test.example.com',
      'domain': 'test.example.com/instance2',
      'image': 'flask-one:1.2-1',
      'port': 'auto',
      },
      ...
     {'actual_port': 8108,
      'domain': 'sloop.example.com',
      'image': 'nua-flask-upload-one:1.0-1',
      'port': 'auto'}]
    """
    sites_list = []
    for host in host_list:
        for site in host["sites"]:
            site["hostname"] = host["hostname"]
            sites_list.append(site)
    return sites_list


def display_deployed(sites: list):
    protocol = protocol_prefix()
    for site in sites:
        msg = f"image '{site['image']}' deployed as {protocol}{site['domain']}"
        print_green(msg)


def configure_service_postgres(site):
    """Configure local postgres on the host.

    Currently:
        - ensure listening on docker gateway
        - restart service
    """
    if not pg_check_listening(docker_host_gateway_ip()):
        print_red(f"Postgresql configuration problem for '{site['image']}'")


def restart_requirements(reboots: set):
    if verbosity(2):
        if reboots:
            print("Services to restart:", pformat(reboots))
        else:
            print("Services to restart: None")
    for service in reboots:
        if service in SERVICE_RESTART:
            restart_function = SERVICE_RESTART[service]
            restart_function()


def configure_service(service: str, site: dict):
    if service == "postgres":
        configure_service_postgres(site)


def _required_services(site: dict) -> set:
    image_nua_config = site["image_nua_config"]
    services = image_nua_config.get("instance", {}).get("services")
    if not services:
        return set()
    if isinstance(services, str):
        services = [services]
    set_services = set(services)
    # filter alias if needed:
    for alias, name in SERVICES_ALIASES.items():
        if alias in set_services:
            set_services.discard(alias)
            set_services.add(name)
    return set_services


def service_requirements(sites: list):
    reboots = set()
    for site in sites:
        services = _required_services(site)
        reboots.update(services)
        for service in services:
            configure_service(service, site)
    restart_requirements(reboots)


def configure_nginx(host_list: list):
    clean_nua_nginx_default_site()
    for host in host_list:
        if verbosity(1):
            print_magenta(f"Configure Nginx for hostname '{host['hostname']}'")
        configure_nginx_hostname(host)


def deploy_nua_sites(deploy_config: str) -> int:
    config_path = Path(deploy_config).expanduser().resolve()
    if verbosity(1):
        print_magenta(f"Deploy sites from: {config_path}")
    with open(config_path, mode="rb") as rfile:
        deploy_sites = tomli.load(rfile)
    # first: check that all images are available:
    if not find_all_images(deploy_sites):
        error("Missing images")
    host_list = sort_per_host(deploy_sites)
    if verbosity(2):
        print("'host_list':\n", pformat(host_list))
    orig_mounted_volumes = store.list_instances_container_active_volumes()
    deactivate_all_sites()
    generate_ports(host_list)
    configure_nginx(host_list)
    sites = host_list_to_sites(host_list)
    if verbosity(2):
        print("'sites':\n", pformat(sites))
    register_certbot_domains(sites)
    install_images(sites)
    service_requirements(sites)
    start_containers(sites)
    # unmount_unused_volumes(orig_mounted_volumes)
    chown_r_nua_nginx()
    nginx_restart()
    display_deployed(sites)
    display_used_volumes()
    display_unused_volumes(orig_mounted_volumes)
