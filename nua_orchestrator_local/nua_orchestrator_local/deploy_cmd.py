"""Nua main scripts.
"""
import sys
from copy import deepcopy
from pathlib import Path
from string import ascii_letters, digits

import docker
import tomli

from . import config
from .archive_search import ArchiveSearch
from .certbot import register_certbot_domains
from .docker_utils import (
    display_one_docker_img,
    docker_run,
    docker_service_start_if_needed,
)
from .nginx_util import (
    chown_r_nua_nginx,
    clean_nua_nginx_default_site,
    configure_nginx_domain,
    nginx_restart,
)
from .rich_console import print_green, print_magenta, print_red
from .search_cmd import parse_app_name, search_docker_tar_local
from .server_utils.net_utils import check_port_available

ALLOW_DOCKER_NAME = set(ascii_letters + digits + "-_.")
# parameters passed as a dict to docker run
RUN_DEFAULT = {
    "auto_remove": True,
    "mem_limit": "1G",
    "container_port": 80,
}


def deploy_nua(app_name: str) -> int:
    """Search, install and launch Nua image.

    (from local registry for now.)"""
    # if app_name.endswith(".toml") and Path(app_name).is_file():
    #     return deploy_nua_sites(app_name)
    print_magenta(f"Deploy image '{app_name}'")
    app, tag = parse_app_name(app_name)
    results = search_docker_tar_local(app, tag)
    if not results:
        print_red(f"No image found for '{app_name}'.")
        sys.exit(1)
    # ensure docker is running
    docker_service_start_if_needed()
    # fixme: take higher version, not fist element:
    img_id, image_config = install_image(results[0])
    deploy_image(img_id, image_config)
    return 0


def install_image(image_path: str | Path) -> tuple:
    path = Path(image_path)
    # image is local, so we can mount it directly
    if not path.is_file():
        raise FileNotFoundError(path)
    arch_search = ArchiveSearch(path)
    image_config = arch_search.nua_config_dict()
    if not image_config:
        print_red(f"Error: image non compatible Nua: {path}.")
        raise ValueError("No Nua config found")
    metadata = image_config["metadata"]
    msg = "Installing: '{title}', ({id} {version})".format(**metadata)
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
    print_green("Intalled image:")
    display_one_docker_img(loaded_img)
    return loaded_img.id, image_config


def deploy_image(img_id: str, image_config: dict):
    # here will used core functions of the orchestrator
    # - see if image is already deployed
    # - see if image got specific deploy configuration
    # - build specifc config for nginx and others
    # - build docker run command
    # - finally execute docker command
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
    site_list = [site for dom in domain_list for site in dom["sites"]]
    used = _configured_ports(site_list)
    for site in site_list:
        port = site.get("port")
        if not port:
            continue
        if port == "auto":
            new_port = _free_port(start_ports, end_ports, used)
            used.add(new_port)
            site["port"] = new_port


def install_images(filtered_sites: list):
    # ensure docker is running
    docker_service_start_if_needed()
    installed = {}
    for site in filtered_sites:
        image_str = site["image"]
        app, tag = parse_app_name(image_str)
        results = search_docker_tar_local(app, tag)
        if not results:
            print_red(f"No image found for '{image_str}'.")
            sys.exit(1)
        img_path = results[0]
        if img_path in installed:
            img_id = installed[img_path][0]
            image_config = deepcopy(installed[img_path][1])
        else:
            # fixme: take higher version, not fist element:
            img_id, image_config = install_image(results[0])
            installed[img_path] = (img_id, image_config)
        site["img_id"] = img_id
        site["image_config"] = image_config


def start_containers(filtered_sites: list):
    for site in filtered_sites:
        image_config = site["image_config"]
        run_params = image_config.get("run", RUN_DEFAULT)
        meta = image_config["metadata"]
        domain = site["domain"]
        prefix = site.get("prefix") or ""
        if prefix:
            prefix = f"-{prefix}"
        name_base = f'{meta["id"]}-{meta["version"]}-{domain}{prefix}'
        name = "".join([x for x in name_base if x in ALLOW_DOCKER_NAME])
        run_params["name"] = name
        if "container_port" in run_params:
            container_port = run_params["container_port"]
            del run_params["container_port"]
        else:
            container_port = 80
        host_port = site["port"]
        ports = {f"{container_port}/tcp": host_port}
        run_params["ports"] = ports
        docker_run(site["img_id"], run_params)


def _sites_per_domains(sites: dict) -> dict:
    """Return a dict of sites/domain.

    key : domain name (full name)
    value : list of web sites of domain
    """
    domains = {}
    for site in sites["site"]:
        domain = site.get("domain", "")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(site)
    # print(pformat(domains))
    return domains


def _make_template_data_list(domains: dict) -> list:
    """Convert dict(domain:sites) to list({domain, sites})."""
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


def filter_prefixed_sites(sites: dict) -> list:
    domain_list = _make_template_data_list(_sites_per_domains(sites))
    _classify_prefixd_sites(domain_list)
    return domain_list


def domain_list_to_sites(domain_list: list) -> list:
    filtered_list = []
    for domain_dict in domain_list:
        for site in domain_dict["sites"]:
            filtered_list.append(site)
    return filtered_list


def configure_nginx(domain_list: list):
    clean_nua_nginx_default_site()
    for domain_dict in domain_list:
        print_magenta(f"Configure Nginx for domain '{domain_dict['domain']}'")
        configure_nginx_domain(domain_dict)


def deploy_nua_sites(sites_path: str) -> int:
    print_magenta("Deployment from sites config")
    with open(sites_path, mode="rb") as rfile:
        sites = tomli.load(rfile)
    domain_list = filter_prefixed_sites(sites)
    generate_ports(domain_list)
    configure_nginx(domain_list)
    filtered_sites = domain_list_to_sites(domain_list)
    register_certbot_domains(filtered_sites)
    install_images(filtered_sites)
    start_containers(filtered_sites)
    chown_r_nua_nginx()
    nginx_restart()
