"""Nua main scripts.
"""
import os
import sys
from pathlib import Path
from pprint import pformat
from string import ascii_letters, digits

import docker
import tomli

from . import config, nua_env
from .actions import jinja2_render_file
from .archive_search import ArchiveSearch
from .docker_utils import (
    display_one_docker_img,
    docker_run,
    docker_service_start_if_needed,
)
from .nginx_util import clean_nua_nginx_default_site, nginx_restart
from .rich_console import print_green, print_magenta, print_red
from .search_cmd import parse_app_name, search_docker_tar_local
from .server_utils.net_utils import check_port_available
from .shell import chown_r

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


def _configured_ports(sites):
    used = set()
    for site in sites["site"]:
        port = site.get("port")
        if not port:
            continue
        if port != "auto":
            used.add(int(port))
    return used


def _free_port(used):
    start = config.read("nua", "ports", "start") or 8100
    end = config.read("nua", "ports", "end") or 9000
    for port in range(start, end):
        if port not in used:
            if check_port_available("127.0.0.1", str(port)):
                return port
    raise RuntimeError("Not enough available port")


def generate_ports(sites: dict):
    used = _configured_ports(sites)
    for site in sites["site"]:
        port = site.get("port")
        if not port:
            continue
        if port == "auto":
            new_port = _free_port(used)
            used.add(new_port)
            site["port"] = new_port


def install_images(sites: dict):
    # ensure docker is running
    docker_service_start_if_needed()
    for site in sites["site"]:
        image_str = site["image"]
        app, tag = parse_app_name(image_str)
        results = search_docker_tar_local(app, tag)
        if not results:
            print_red(f"No image found for '{image_str}'.")
            sys.exit(1)
        # fixme: take higher version, not fist element:
        img_id, image_config = install_image(results[0])
        site["img_id"] = img_id
        site["image_config"] = image_config


def start_containers(sites: dict):
    for site in sites["site"]:
        image_config = site["image_config"]
        run_params = image_config.get("run", RUN_DEFAULT)
        meta = image_config["metadata"]
        name_base = f'{meta["id"]}-{meta["version"]}-{site["prefix"]}'
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


def _sites_per_domains(sites):
    domains = {}
    for site in sites["site"]:
        domain = site.get("domain", "")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(site)
    # print(pformat(domains))
    return domains


def _make_template_data(domains):
    data = []
    for domain, content in domains.items():
        dom_dict = {"domain": domain, "sites": []}
        for site in content:
            dom_dict["sites"].append(site)
        data.append(dom_dict)
    return data


def configure_nginx(sites: dict):
    domains = _sites_per_domains(sites)
    data = _make_template_data(domains)
    template = Path(__file__).parent.resolve() / "config" / "nginx" / "domain_template"
    sites_path = nua_env.nginx_path() / "sites"
    clean_nua_nginx_default_site()
    for dom_dict in data:
        print_magenta(f"Configure Nginx for domain '{dom_dict['domain']}'")
        # print(pformat(dom_dict))
        dest_path = sites_path / dom_dict["domain"]
        jinja2_render_file(template, dest_path, dom_dict)
        os.chmod(dest_path, 0o644)
        chown_r(dest_path, "nua", "nua")


def deploy_nua_sites(sites_path: str) -> int:
    print_magenta("Deployment from sites config")
    with open(sites_path, mode="rb") as rfile:
        sites = tomli.load(rfile)
    generate_ports(sites)
    install_images(sites)
    start_containers(sites)
    configure_nginx(sites)
    nginx_restart()
