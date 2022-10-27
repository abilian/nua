"""class to manage the deployment of a group os sites
"""
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from typing import Callable

import tomli

from . import config
from .certbot import protocol_prefix, register_certbot_domains
from .db import store
from .db.model.instance import RUNNING
from .deploy_utils import (
    add_host_gateway,
    load_install_image,
    mount_volumes,
    port_allocator,
    unused_volumes,
    volume_print,
)
from .docker_utils import (
    docker_remove_container_db,
    docker_run,
    docker_service_start_if_needed,
)
from .domain_split import DomainSplit
from .nginx_util import (
    chown_r_nua_nginx,
    clean_nua_nginx_default_site,
    configure_nginx_hostname,
    nginx_restart,
)
from .panic import error
from .resource import Resource
from .rich_console import print_green, print_magenta, print_red
from .search_cmd import search_nua
from .service_loader import Services
from .site import Site
from .state import verbosity

# parameters passed as a dict to docker run
RUN_BASE = {
    "extra_hosts": {"host.docker.internal": "host-gateway"},
}


class SitesDeployment:
    def __init__(self):
        self.required_services = []
        self.deploy_sites = {}
        self.host_list = []
        self.available_services = {}
        self.orig_mounted_volumes = []
        self.sites = []

    def load_available_services(self):
        # assuming db_setup was run at initialization of the command
        services = Services()
        services.load()
        self.available_services = services.loaded
        if verbosity(2):
            print_magenta(
                f"Available services: {pformat(list(services.loaded.keys()))}"
            )

    def load_deploy_config(self, deploy_config: str):
        config_path = Path(deploy_config).expanduser().resolve()
        if verbosity(1):
            print_magenta(f"Deploy sites from: {config_path}")
        deploy_sites_config = tomli.loads(config_path.read_text())
        self.deploy_sites = self.build_deploy_sites(deploy_sites_config)
        self.host_list = self.build_host_list()

    def build_deploy_sites(self, deploy_sites_config: dict):
        """Check config syntax, replace missing informations by defaults."""
        sites = []
        for site_dict in deploy_sites_config["site"]:
            if not isinstance(site_dict, dict):
                raise ValueError(f"Site configuration must be a dict: '{site_dict}'")
            site = Site(site_dict)
            site.check_valid()
            site.set_ports_as_dict()
            sites.append(site)
        return sites

    def build_host_list(self) -> list:
        host_list = self._make_host_list()
        _classify_located_sites(host_list)
        return host_list

    def _make_host_list(self) -> list:
        """Convert dict(hostname:[sites,..]) to list({hostname, sites}).

        ouput format:
        [{'hostname': 'test.example.com',
         'sites': [{'domain': 'test.example.com/instance1',
                     'image': 'flask-one:1.2-1',
                     },
                    {'domain': 'test.example.com/instance2',
                     'image': 'flask-one:1.2-1',
                     },
                     ...
         {'hostname': 'sloop.example.com',
          'sites': [{'domain': 'sloop.example.com',
                     'image': 'nua-flask-upload-one:1.0-1',
                     }]}]
        """
        sites_per_host = self._sites_per_host()
        return [
            {"hostname": hostname, "sites": sites_list}
            for hostname, sites_list in sites_per_host.items()
        ]

    def _sites_per_host(self) -> dict:
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


        ouput format: dict of hostnames, with explicit port = "auto".

        {'sloop.example.com': [{'domain': 'sloop.example.com',
                              'image': 'nua-flask-upload-one:1.0-1',
                              }],
        'test.example.com': [{'domain': 'test.example.com/instance1',
                             'image': 'flask-one:1.2-1',
                             },
                             ...
        """
        hostnames = {}
        for site in self.deploy_sites:
            dom = DomainSplit(site.domain)
            if dom.hostname not in hostnames:
                hostnames[dom.hostname] = []
            hostnames[dom.hostname].append(site)
        return hostnames

    def host_list_to_sites(self) -> list:
        """Convert to list of sites format.

        output format:
        [{'host_port': 8100,
          'hostname': 'test.example.com',
          'domain': 'test.example.com/instance1',
          'location': 'instance1',
          'image': 'flask-one:1.2-1',
          'ports': {...},
         {'host_port': 8101,
          'hostname': 'test.example.com',
          'domain': 'test.example.com/instance2',
          'image': 'flask-one:1.2-1',
          'ports': {...},
          },
          ...
         {'host_port': 8108,
          'domain': 'sloop.example.com',
          'image': 'nua-flask-upload-one:1.0-1',
          'ports': {...}]
        """
        sites_list = []
        for host in self.host_list:
            for site in host["sites"]:
                site.hostname = host["hostname"]
                sites_list.append(site)
        return sites_list

    def install_required_images(self):
        # first: check that all images are available:
        if not self.find_all_images():
            error("Missing images")
        self.install_images()

    def find_all_images(self) -> bool:
        images_found = set()
        for site in self.deploy_sites:
            if site.image in images_found:
                continue
            results = search_nua(site.image)
            if not results:
                print_red(f"No image found for '{site.image}'.")
                return False
            images_found.add(site.image)
            if verbosity(1):
                print_red(f"image found: '{site.image}'.")
        return True

    def install_images(self):
        # ensure docker is running
        docker_service_start_if_needed()
        installed = {}
        for site in self.deploy_sites:
            results = search_nua(site.image)
            if not results:
                error(f"No image found for '{site.image}'. Exiting.")
            # results are sorted by version, take higher:
            img_path = results[-1]
            if img_path in installed:
                image_id = installed[img_path][0]
                image_nua_config = deepcopy(installed[img_path][1])
            else:
                image_id, image_nua_config = load_install_image(img_path)
                installed[img_path] = (image_id, image_nua_config)
            site["image_id"] = image_id
            site.image_nua_config = image_nua_config

    def deactivate_all_sites(self):
        """Find all instance in DB
        - remove container if exists
        - remove site from DB
        """
        self.orig_mounted_volumes = store.list_instances_container_active_volumes()
        instances = store.list_instances_all()
        for instance in instances:
            if verbosity(2):
                print(
                    f"Removing from containers and DB: "
                    f"'{instance.app_id}' instance on '{instance.domain}'"
                )
            docker_remove_container_db(instance.domain)

    def configure_deployment(self):
        self.sites = self.host_list_to_sites()
        self.generate_ports()
        self.configure_nginx()
        if verbosity(2):
            print("'sites':\n", pformat(self.sites))
        register_certbot_domains(self.sites)
        self.check_services()
        self.restart_services()

    def check_services(self):
        for site in self.sites:
            site.normalize_required_services(self.available_services)
            for service in site.required_services:
                handler = self.available_services[service]
                if not handler.check_site_configuration(site):
                    print_red(
                        f"Service '{service}': configuration problem for '{site.image}'"
                    )

    def restart_services(self):
        reboots = set()
        for site in self.sites:
            reboots.update(site.required_services)
        if verbosity(2):
            if reboots:
                print("Services to restart:", pformat(reboots))
            else:
                print("Services to restart: None")
        for service in reboots:
            handler = self.available_services[service]
            handler.restart()

    def configure_nginx(self):
        clean_nua_nginx_default_site()
        for host in self.host_list:
            if verbosity(1):
                print_magenta(f"Configure Nginx for hostname '{host['hostname']}'")
            configure_nginx_hostname(host)

    def generate_ports(self):
        start_ports = config.read("nua", "ports", "start") or 8100
        end_ports = config.read("nua", "ports", "end") or 9000
        if verbosity(4):
            print(
                f"generate_ports(): auto addresses in interval {start_ports} to {end_ports}"
            )
        self.update_ports_from_nua_config()
        allocated_ports = self._configured_ports()
        if verbosity(4):
            print(f"generate_ports(): {allocated_ports=}")
        # list of ports used for domains / sites, trying to keep them unchanged
        ports_instances_domains = store.ports_instances_domains()
        if verbosity(4):
            print(f"generate_ports(): {ports_instances_domains=}")
        allocated_ports.update(ports_instances_domains)
        if verbosity(3):
            print(f"generate_ports() used ports:\n {allocated_ports=}")
        self.generate_ports_for_sites(
            port_allocator(start_ports, end_ports, allocated_ports)
        )

    def _configured_ports(self) -> set[int]:
        """
        Return set of required host ports (aka non auto ports) from site_list.

        Returns: set of integers

        Expected format for ports:
        ports = {
            "80":{
                "container": 80,
                "host": "auto",
                "protocol": "tcp",
                "proxy": "auto"
                },
            ...
        }
        """
        used = set()
        for site in self.sites:
            try:
                used.update(site.used_ports())
            except (ValueError, IndexError) as e:
                print_red("Error for site config:", e)
                print(pformat(site))
                raise
        return used

    def generate_ports_for_sites(self, allocator: Callable):
        """
        Update site dict with auto generated ports.
        """
        for site in self.sites:
            site.allocate_auto_ports(allocator)

    def update_ports_from_nua_config(self):
        """If port not declared in site config, use image definition.

        Merge ports modifications from site config with image config.
        """
        if verbosity(5):
            print(f"update_ports_from_nua_config(): len(site_list)= {len(self.sites)}")
        for site in self.sites:
            site.rebase_ports_upon_nua_config()

    def start_sites(self):
        for site in self.sites:
            self.start_one_container(site)
            self.store_container_instance(site)
        chown_r_nua_nginx()
        nginx_restart()

    def start_one_container(self, site: Site):
        run_params = self.generate_container_run_parameters(site)
        if verbosity(4):
            print(f"start_one_container(): {run_params=}")
        # volumes need to be mounted before beeing passed as arguments to
        # docker.run()
        mounted_volumes = mount_volumes(site)
        if mounted_volumes:
            run_params["mounts"] = mounted_volumes
        site.run_params = run_params
        docker_run(site)
        if mounted_volumes:
            site.run_params["mounts"] = True
        if verbosity(1):
            print_magenta(f"    -> run new container         '{site['container']}'")

    def store_container_instance(self, site):
        meta = site.image_nua_config["metadata"]
        store.store_instance(
            app_id=meta["id"],
            nua_tag=store.nua_tag_string(meta),
            domain=site.domain,
            container=site["container"],
            image=site.image,
            state=RUNNING,
            site_config=dict(site),
        )

    def generate_container_run_parameters(self, site: Site):
        """Return suitable parameters for the docker.run() command."""
        image_nua_config = site.image_nua_config
        run_params = deepcopy(RUN_BASE)
        docker_default_run = config.read("nua", "docker_default_run")
        if verbosity(4):
            print(f"generate_container_run_parameters(): {docker_default_run=}")
        run_params.update(docker_default_run)
        run_params.update(image_nua_config.get("run", {}))
        add_host_gateway(run_params)
        run_params["name"] = site.container_name
        run_params["ports"] = site.ports_as_docker_params()
        run_params["environment"] = self.run_parameters_container_environment(site)
        return run_params

    def run_parameters_container_environment(self, site: Site) -> dict:
        image_nua_config = site.image_nua_config
        run_env = image_nua_config.get("run_env", {})
        run_env.update(self.services_environment(site))
        run_env.update(site.run_env)
        return run_env

    def services_environment(self, site: Site) -> dict:
        run_env = {}
        for service in site.required_services:
            handler = self.available_services[service]
            # function may need or not site param:
            run_env.update(handler.environment(site))
        return run_env

    def display_final(self):
        self.display_deployed()
        self.display_used_volumes()
        self.display_unused_volumes()

    def display_deployed(self):
        protocol = protocol_prefix()
        for site in self.sites:
            msg = f"image '{site.image}' deployed as {protocol}{site.domain}"
            print_green(msg)

    def display_used_volumes(self):
        if not verbosity(1):
            return
        current_mounted = store.list_instances_container_active_volumes()
        if not current_mounted:
            return
        print_green("Volumes used by current Nua configuration:")
        for volume in current_mounted:
            volume_print(volume)

    def display_unused_volumes(self):
        if not verbosity(1):
            return
        unused = unused_volumes(self.orig_mounted_volumes)
        if not unused:
            return
        print_green(
            "Some volumes are mounted but not used by current Nua configuration:"
        )
        for volume in unused:
            volume_print(volume)


def _classify_located_sites(host_list: list):
    """Return sites classified for location use.

    For a domain:
        - either only one site:
            www.example.com -> site
        - either all sites must have a location (path):
            www.example.com/path1 -> site1
            www.example.com/path2 -> site2

    So, if not located, check it is the only one site of the domain.
    The method checks the cohereence and add a located 'flag'
    """

    for host in host_list:
        sites_list = host["sites"]
        first = sites_list[0]  # by construction, there is at least 1 element
        dom = DomainSplit(first.domain)
        if dom.location:
            _verify_located(host)
        else:
            _verify_not_located(host)


def _verify_located(host: dict):
    """host format:
     {'hostname': 'test.example.com',
      'sites': [{'domain': 'test.example.com/instance1',
                  'image': 'flask-one:1.2-1',
                  # 'port': 'auto',
                  },
                 {'domain': 'test.example.com/instance2',
                  'image': 'flask-one:1.2-1',
                  ...
    changed to:
    {'hostname': 'test.example.com',
     'located': True,
     'sites': [{'domain': 'test.example.com/instance1',
                 'image': 'flask-one:1.2-1',
                 # 'port': 'auto',
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
        dom = DomainSplit(site.domain)
        if not dom.location:
            image = site.image
            print_red("Error: required location is missing, site discarded:")
            print_red(f"    for {hostname=} / {image=}")
            continue
        if dom.location in known_location:
            image = site.image
            # port = site.get("port")
            print_red("Error: location is already used for a domain, site discarded:")
            print_red(f"    {hostname=} / {image=} / {site.domain}")
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
            image = site.image
            print_red(f"    {image=} / {site['domain']}")
    host["sites"] = valid
    host["located"] = False