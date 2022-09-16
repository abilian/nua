"""Nua main scripts.

Rem: maybe need to refactor the "site" thing into a class and refactor a lot
"""
import sys
from copy import deepcopy
from pathlib import Path
from pprint import pformat

# from pprint import pprint
from string import ascii_letters, digits

import docker
import tomli

from .. import config
from ..archive_search import ArchiveSearch
from ..certbot import register_certbot_domains
from ..db import store
from ..docker_utils import (
    display_one_docker_img,
    docker_host_gateway_ip,
    docker_run,
    docker_service_start_if_needed,
    docker_volume_create_or_use,
)
from ..nginx_util import (
    chown_r_nua_nginx,
    clean_nua_nginx_default_site,
    configure_nginx_domain,
    nginx_restart,
)
from ..postgres import pg_check_listening, pg_restart_service, pg_run_environment
from ..rich_console import print_green, print_magenta, print_red
from ..search_cmd import parse_app_name, search_docker_tar_local
from ..server_utils.net_utils import check_port_available
from ..state import verbosity

ALLOW_DOCKER_NAME = set(ascii_letters + digits + "-_.")
# parameters passed as a dict to docker run
RUN_BASE = {
    "auto_remove": True,
    "extra_hosts": {"host.docker.internal": "host-gateway"},
}
RUN_DEFAULT = {
    "mem_limit": "1G",
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
    print_magenta(f"verbosityy image '{app_name}'")
    app, tag = parse_app_name(app_name)
    results = search_docker_tar_local(app, tag)
    if not results:
        print_red(f"No image found for '{app_name}'.")
        sys.exit(1)
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


def generate_ports(domain_list: list):
    start_ports = config.read("nua", "ports", "start") or 8100
    end_ports = config.read("nua", "ports", "end") or 9000
    if verbosity(3):
        print(f"generate_ports from {start_ports} to {end_ports}")
    site_list = [site for dom in domain_list for site in dom["sites"]]
    used = _configured_ports(site_list)
    # list of ports used for domains / sites, trying to keep them inchanged
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
        # current_instance_port = store.instance_port(site["domain"], site["prefix"])
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
        app, tag = parse_app_name(image_str)
        results = search_docker_tar_local(app, tag)
        if not results:
            print_red(f"No image found for '{image_str}'. Exiting.")
            sys.exit(1)
        img_path = results[-1]  # results are sorted by version, take higher
        if img_path in installed:
            image_id = installed[img_path][0]
            image_nua_config = deepcopy(installed[img_path][1])
        else:
            image_id, image_nua_config = install_image(img_path)
            installed[img_path] = (image_id, image_nua_config)
        site["image_id"] = image_id
        site["image_nua_config"] = image_nua_config


def create_docker_volumes(volumes_config):
    # docker_volumes = []
    for volume_params in volumes_config:
        # docker_volumes.append(docker_volume_create_or_use(volume_params))
        docker_volume_create_or_use(volume_params)


def mount_volumes(site: dict):
    image_nua_config = site["image_nua_config"]
    volumes_config = image_nua_config.get("volume") or []
    create_docker_volumes(volumes_config)
    mounted_volumes = []
    for volume_params in volumes_config:
        mounted_volumes.append(
            docker.types.Mount(
                volume_params["target"],
                volume_params["source"],
                type=volume_params["type"],
            )
        )
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
    domain = site["domain"]
    prefix = site.get("prefix") or ""
    str_prefix = f"-{prefix}" if prefix else ""
    app_name = nua_long_name(meta)
    name_base = f"{app_name}-{domain}{str_prefix}"
    return "".join([x for x in name_base if x in ALLOW_DOCKER_NAME])


def _run_parameters_container_ports(site: dict, run_params: dict) -> dict:
    # fixme: first version does force at least a port
    if "container_port" in run_params:
        container_port = run_params["container_port"]
        del run_params["container_port"]
    else:
        container_port = 80
    host_port = site["actual_port"]
    ports = {f"{container_port}/tcp": host_port}
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


def stop_previous_containers(sites: list):
    pass


def _sites_per_domains(deploy_sites: dict) -> dict:
    """Return a dict of sites/domain.

    key : domain name (full name)
    value : list of web sites of domain

    input format:
    [[site]]
    domain = "test.example.com"
    image = "flask-one:1.2-1"
    prefix = "instance1"
    port = "auto"
    [[site]]
    domain = "sloop.example.com"
    image = "nua-flask-upload-one:1.0-1"
    port = "auto"

    ouput format:
    {'sloop.example.com': [{'domain': 'sloop.example.com',
                          'image': 'nua-flask-upload-one:1.0-1',
                          'port': 'auto',
                          'prefix': ''}],
    'test.example.com': [{'domain': 'test.example.com',
                         'image': 'flask-one:1.2-1',
                         'port': 'auto',
                         'prefix': 'instance1'},
                         ...
    """
    domains = {}
    for site in deploy_sites["site"]:
        site["prefix"] = site.get("prefix", "").strip()
        domain = site.get("domain", "").strip()
        site["domain"] = domain.strip()
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(site)
    return domains


def _make_template_data_list(domains: dict) -> list:
    """Convert dict(domain:[sites,..]) to list({domain, sites}).

    ouput format:
    [{'domain': 'test.example.com',
     'sites': [{'domain': 'test.example.com',
                 'image': 'flask-one:1.2-1',
                 'port': 'auto',
                 'prefix': 'instance1',
                {'domain': 'test.example.com',
                 'image': 'flask-one:1.2-1',
                 'port': 'auto',
                 'prefix': 'instance2'},
                 ...
     {'domain': 'sloop.example.com',
      'sites': [{'domain': 'sloop.example.com',
                 'image': 'nua-flask-upload-one:1.0-1',
                 'port': 'auto'}]}]
    """
    return [
        {"domain": domain, "sites": sites_list}
        for domain, sites_list in domains.items()
    ]


def _classify_prefixd_sites(data: list):
    """Return sites classified for prefix use, verify it is the only one of the domain."""
    for domain_dict in data:
        sites_list = domain_dict["sites"]
        first = sites_list[0]  # by construction, there is at least 1 element
        if first.get("prefix"):
            _verify_prefixed(domain_dict)
        else:
            _verify_not_prefixed(domain_dict)


def _verify_prefixed(domain_dict: dict):
    known_prefix = set()
    valid = []
    for site in domain_dict["sites"]:
        prefix = site.get("prefix")
        if not prefix:
            domain = domain_dict["domain"]
            image = site.get("image")
            port = site.get("port")
            print_red("Error: required prefix is missing, site discarded:")
            print_red(f"    for {domain=} / {image=} / {port=}")
            continue
        if prefix in known_prefix:
            domain = domain_dict["domain"]
            image = site.get("image")
            port = site.get("port")
            print_red("Error: prefix is already used for this domain, site discarded:")
            print_red(f"    {domain=} / {image=} / {port=}")
            continue
        known_prefix.add(prefix)
        valid.append(site)
    domain_dict["sites"] = valid
    domain_dict["prefixed"] = True


def _verify_not_prefixed(domain_dict: dict):
    # we know that the first of the list is not prefixed. We expect the list
    # has only one site.
    if len(domain_dict["sites"]) == 1:
        valid = domain_dict["sites"]
    else:
        domain = domain_dict["domain"]
        valid = []
        valid.append(domain_dict["sites"].pop(0))
        print_red(f"Error: too many sites for {domain=}, site discarded:")
        for site in domain_dict["sites"]:
            prefix = site.get("prefix")
            image = site.get("image")
            port = site.get("port")
            print_red(f"    {image=} / {prefix=} / {port=}")
    domain_dict["sites"] = valid
    domain_dict["prefixed"] = False


def sort_per_domain(deploy_sites: dict) -> list:
    domain_list = _make_template_data_list(_sites_per_domains(deploy_sites))
    _classify_prefixd_sites(domain_list)
    return domain_list


def domain_list_to_sites(domain_list: list) -> list:
    """Convert to list of sites format.

    output format:
    [{'actual_port': 8100,
      'domain': 'test.example.com',
      'image': 'flask-one:1.2-1',
      'port': 'auto',
      'prefix': 'instance1',
     {'actual_port': 8101,
      'domain': 'test.example.com',
      'image': 'flask-one:1.2-1',
      'port': 'auto',
      'prefix': 'instance2'},
      ...
     {'actual_port': 8108,
      'domain': 'sloop.example.com',
      'image': 'nua-flask-upload-one:1.0-1',
      'port': 'auto'}]
    """
    filtered_list = []
    for domain_dict in domain_list:
        for site in domain_dict["sites"]:
            filtered_list.append(site)
    return filtered_list


def display_deployed(sites: list):
    for site in sites:
        prefix = f"/{site['prefix']}" if site.get("prefix") else ""
        url = f"https://{site['domain']}{prefix}"
        msg = f"image '{site['image']}' deployed as {url}"
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
        print("Services to restart:", pformat(reboots))
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


def configure_nginx(domain_list: list):
    clean_nua_nginx_default_site()
    for domain_dict in domain_list:
        if verbosity(1):
            print_magenta(f"Configure Nginx for domain '{domain_dict['domain']}'")
        configure_nginx_domain(domain_dict)


def deploy_nua_sites(deploy_config: str) -> int:
    config_path = Path(deploy_config).expanduser().resolve()
    if verbosity(1):
        print_magenta(f"Deploy sites from: {config_path}")
    with open(config_path, mode="rb") as rfile:
        deploy_sites = tomli.load(rfile)
    domain_list = sort_per_domain(deploy_sites)
    if verbosity(2):
        print("'domain_list':\n", pformat(domain_list))
    generate_ports(domain_list)
    configure_nginx(domain_list)
    sites = domain_list_to_sites(domain_list)
    if verbosity(2):
        print("'sites':\n", pformat(sites))
    register_certbot_domains(sites)
    install_images(sites)
    service_requirements(sites)
    start_containers(sites)
    chown_r_nua_nginx()
    nginx_restart()
    display_deployed(sites)
