"""class to manage the deployment of a group os sites."""
import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from pprint import pformat

import tomli
from nua.lib.console import print_green, print_magenta, print_red
from nua.lib.panic import abort, info, warning
from nua.lib.tool.state import verbosity

from . import config
from .certbot import protocol_prefix, register_certbot_domains
from .db import store
from .db.model.deployconfig import ACTIVE, INACTIVE, PREVIOUS
from .db.model.instance import RUNNING
from .deploy_utils import (
    create_container_private_network,
    deactivate_all_instances,
    deactivate_site,
    extra_host_gateway,
    load_install_image,
    mount_resource_volumes,
    port_allocator,
    pull_resource_container,
    start_container_engine,
    start_one_container,
    unused_volumes,
)
from .domain_split import DomainSplit
from .healthcheck import HealthCheck
from .nginx_util import (
    chown_r_nua_nginx,
    clean_nua_nginx_default_site,
    configure_nginx_hostname,
    nginx_restart,
)
from .requirement_evaluator import instance_key_evaluator
from .resource import Resource
from .service_loader import Services
from .site import Site
from .volume import Volume

# parameters passed as a dict to docker run
RUN_BASE = {}  # see also nua_config
RUN_BASE_RESOURCE = {"restart_policy": {"name": "always"}}


class SitesDeployment:
    """Deployment of a list of site/nua-image.

    Devel notes: will be refactored into base class and sub classes for various
    deployment strategies (restoring previous configuration, ...).

    example of use:
        deployer = SitesDeployment()
        deployer.local_services_inventory()
        deployer.load_deploy_config(deploy_config)
        deployer.gather_requirements()
        deployer.configure()
        deployer.deactivate_previous_sites()
        deployer.apply_configuration()
        deployer.start_sites()
        deployer.post_deployment()
    """

    def __init__(self):
        self.loaded_config = {}
        self.sites = []
        self.sites_per_domain = []
        self.required_services = set()
        self.available_services = {}
        self.orig_mounted_volumes = []
        self.previous_config_id = 0
        # self.future_config_id = 0

    @staticmethod
    def previous_success_deployment_record() -> dict:
        previous_config = store.deploy_config_active()
        if previous_config:
            return previous_config
        else:
            # either
            # - first run or
            # - last deployment did crash with a PREVIOUS status somewhere
            # - or rare situation (active->inactive)
            previous_config = store.deploy_config_previous()
            if previous_config:
                return previous_config
        return store.deploy_config_last_inactive()

    def store_deploy_configs_before_swap(self):
        """Fetch previous configuration before installing the new one."""
        previous_config = self.previous_success_deployment_record()
        self.previous_config_id = previous_config.get("id", 0)
        if previous_config and previous_config["state"] != PREVIOUS:
            store.deploy_config_update_state(self.previous_config_id, PREVIOUS)
        # deploy_config = {
        #     "requested": self.loaded_config,
        #     "sites": deepcopy(self.sites),
        # }
        # self.future_config_id = store.deploy_config_add_config(
        #     deploy_config, self.previous_config_id, INACTIVE
        # )

    def store_deploy_configs_after_swap(self):
        """Store configurations' status if the new configuration is
        successfully installed."""
        # previous config stay INACTIVE
        if self.previous_config_id:
            store.deploy_config_update_state(self.previous_config_id, INACTIVE)
        # store.deploy_config_update_state(self.future_config_id, ACTIVE)
        deploy_config = {
            "requested": self.loaded_config,
            "sites": deepcopy(self.sites),
        }
        self.future_config_id = store.deploy_config_add_config(
            deploy_config, self.previous_config_id, ACTIVE
        )

    def local_services_inventory(self):
        """Initialization step: inventory of available resources available on
        the host, like local databases."""
        # See later
        return
        # assuming db_setup was run at initialization of the command
        services = Services()
        services.load()
        self.available_services = services.loaded
        if verbosity(2):
            print_magenta(
                f"Available local services: {pformat(list(services.loaded.keys()))}"
            )

    def load_deploy_config(self, deploy_config: str):
        config_path = Path(deploy_config).expanduser().resolve()
        if verbosity(1):
            info(f"Deploy sites from: {config_path}")
        self.loaded_config = tomli.loads(config_path.read_text())
        self.parse_deploy_sites()
        self.sort_sites_per_domain()
        if verbosity(3):
            self.print_host_list()

    def restore_previous_deploy_config_strict(self):
        """Retrieve last successful deployment configuration (strict mode)."""
        if verbosity(1):
            info("Deploy sites from previous deployment (strict mode).")
        previous_config = self.previous_success_deployment_record()
        if not previous_config:
            abort("Impossible to find a previous deployment.")
        self.loaded_config = previous_config["deployed"]["requested"]
        self.sites = []
        for site_dict in previous_config["deployed"]["sites"]:
            self.sites.append(Site.from_dict(site_dict))
        # self.future_config_id = previous_config.get("id")
        self.sort_sites_per_domain()

    def restore_previous_deploy_config_replay(self):
        """Retrieve last successful deployment configuration (replay mode)."""
        if verbosity(1):
            info("Deploy sites from previous deployment (replay deployment).")
        previous_config = self.previous_success_deployment_record()
        if not previous_config:
            abort("Impossible to find a previous deployment.")
        self.loaded_config = previous_config["deployed"]["requested"]
        # self.future_config_id = previous_config.get("id")
        self.parse_deploy_sites()
        self.sort_sites_per_domain()
        if verbosity(3):
            self.print_host_list()

    def gather_requirements(self):
        self.install_required_images()
        self.install_required_resources()

    def configure(self):
        self.set_network_names()
        self.merge_instances_to_resources()
        self.set_volumes_names()
        self.check_required_local_resources()
        for site in self.sites:
            site.set_ports_as_dict()
        for site in self.sites:
            site.parse_healthcheck()
        for site in self.sites:
            self.check_required_local_resources_configuration(site)
        for site in self.sites:
            self.retrieve_persistent(site)
        # We now allocate ports *before* stopping services, thus this may induce
        # a flip/flop balance when reinstalling same config
        self.generate_ports()

    def restore_configure(self):
        """Try to reuse the previous configuration with no change."""
        self.check_required_local_resources()
        for site in self.sites:
            self.check_required_local_resources_configuration(site)

    def deactivate_previous_sites(self):
        """Find all instance in DB.

        - remove container if exists
        - remove site from Nua DB
        """
        self.store_deploy_configs_before_swap()
        self.orig_mounted_volumes = store.list_instances_container_active_volumes()
        deactivate_all_instances()

    def restore_deactivate_previous_sites(self):
        """For restore situation, find all instance in DB.

        - remove container if exists
        - remove site from Nua DB
        """
        self.orig_mounted_volumes = store.list_instances_container_active_volumes()
        deactivate_all_instances()

    def apply_configuration(self):
        """Apply configuration, especially configurations that can not be
        deployed before all previous sites are stopped."""
        self.configure_nginx()
        # registering https sites with certbot requires that the base nginx config is
        # deployed.
        register_certbot_domains(self.sites)
        if verbosity(2):
            print("'sites':\n", pformat(self.sites))

    def start_sites(self):
        """Start all sites to deploy."""
        # restarting local services:
        self.restart_local_services()
        for site in self.sites:
            deactivate_site(site)
            self.start_network(site)
            self.set_container_names(site)
            self.evaluate_container_params(site)
            self.start_resources_containers(site)
            self.start_main_site_container(site)
            self.store_container_instance(site)
        chown_r_nua_nginx()
        nginx_restart()

    def parse_deploy_sites(self):
        """Make the list of Sites.

        Check config syntax, replace missing informations by defaults.
        """
        sites = []
        for site_dict in self.loaded_config["site"]:
            if not isinstance(site_dict, dict):
                abort(
                    "Site configuration must be a dict",
                    explanation=f"{pformat(site_dict)}",
                )
            site = Site(site_dict)
            site.check_valid()
            # site.set_ports_as_dict()
            sites.append(site)
        self.sites = sites

    def sort_sites_per_domain(self):
        """Classify the sites per domain, filtering out miss declared sites.

        The sites per domain are available in self.sites_per_domain
        """
        self._make_sites_per_domain()
        self._filter_miss_located_sites()
        self._update_sites_list()

    def _make_sites_per_domain(self):
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
        sites_per_domain = self._sites_per_domain()
        self.sites_per_domain = [
            {"hostname": hostname, "sites": sites_list}
            for hostname, sites_list in sites_per_domain.items()
        ]

    def _sites_per_domain(self) -> dict:
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
        sites_per_domain = {}
        for site in self.sites:
            dom = DomainSplit(site.domain)
            if dom.hostname not in sites_per_domain:
                sites_per_domain[dom.hostname] = []
            sites_per_domain[dom.hostname].append(site)
        return sites_per_domain

    def _filter_miss_located_sites(self):
        """Return sites classified for location use.

        For a domain:
            - either only one site:
                www.example.com -> site
            - either all sites must have a location (path):
                www.example.com/path1 -> site1
                www.example.com/path2 -> site2

        So, if not located, check it is the only one site of the domain.
        The method checks the coherence and add a located 'flag'
        """
        for host in self.sites_per_domain:
            sites_list = host["sites"]
            first = sites_list[0]  # by construction, there is at least 1 element
            dom = DomainSplit(first.domain)
            if dom.location:
                _verify_located(host)
            else:
                _verify_not_located(host)

    def _update_sites_list(self):
        """Rebuild the list of Site from filtered sites per domain."""
        sites_list = []
        for host in self.sites_per_domain:
            for site in host["sites"]:
                site.hostname = host["hostname"]
                sites_list.append(site)
        self.sites = sites_list

    def install_required_images(self):
        # first: check that all Nua images are available:
        if not self.find_all_images():
            abort("Missing Nua images")
        self.install_images()

    def find_all_images(self) -> bool:
        for site in self.sites:
            if not site.find_registry_path():
                print_red(f"No image found for '{site.image}'")
                return False
        if verbosity(1):
            seen = set()
            for site in self.sites:
                if site.image not in seen:
                    seen.add(site.image)
                    info(f"image found: '{site.image}'")
        return True

    def install_images(self):
        start_container_engine()
        installed = {}
        for site in self.sites:
            if not site.find_registry_path(cached=True):
                abort(f"No image found for '{site.image}'")
            registry_path = site.registry_path
            if registry_path in installed:
                image_id = installed[registry_path][0]
                image_nua_config = deepcopy(installed[registry_path][1])
            else:
                image_id, image_nua_config = load_install_image(registry_path)
                installed[registry_path] = (image_id, image_nua_config)
            site.image_id = image_id
            site.image_nua_config = image_nua_config

    def install_required_resources(self):
        for site in self.sites:
            site.parse_resources()
            site.set_ports_as_dict()
        if not self.pull_all_resource_images():
            abort("Missing Docker images")

    def pull_all_resource_images(self) -> bool:
        return all(
            all(self._pull_resource(resource) for resource in site.resources)
            for site in self.sites
        )

    def _pull_resource(self, resource: Resource) -> bool:
        if resource.type == "local":
            # will check later in the process
            return True
        return pull_resource_container(resource)

    def check_required_local_resources(self):
        self.required_services = {s for site in self.sites for s in site.local_services}
        if verbosity(3):
            print("required services:", self.required_services)
        available_services = set(self.available_services.keys())
        for service in self.required_services:
            if service not in available_services:
                abort(f"Required service '{service}' is not available")

    def check_required_local_resources_configuration(self, site: Site):
        for service in site.local_services:
            handler = self.available_services[service]
            if not handler.check_site_configuration(site):
                abort(
                    f"Required service '{service}' not configured for site {site.domain}"
                )

    def set_network_names(self):
        for site in self.sites:
            site.set_network_name()
        if verbosity(3):
            print("set_network_names() done")

    def merge_instances_to_resources(self):
        for site in self.sites:
            site.merge_instance_to_resources()
        if verbosity(3):
            print("merge_instances_to_resources() done")

    def set_volumes_names(self):
        for site in self.sites:
            site.set_volumes_names()

    def restart_local_services(self):
        if verbosity(2):
            if self.required_services:
                info("Services to restart:", pformat(self.required_services))
            else:
                info("Services to restart: None")
        for service in self.required_services:
            handler = self.available_services[service]
            handler.restart()

    def configure_nginx(self):
        clean_nua_nginx_default_site()
        for host in self.sites_per_domain:
            if verbosity(1):
                info(f"Configure Nginx for hostname '{host['hostname']}'")
            configure_nginx_hostname(host)

    def generate_ports(self):
        start_ports = config.read("nua", "ports", "start") or 8100
        end_ports = config.read("nua", "ports", "end") or 9000
        if verbosity(4):
            print(
                f"generate_ports(): addresses in interval {start_ports} to {end_ports}"
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
        if verbosity(3):
            print("generate_ports() done")

    def _configured_ports(self) -> set[int]:
        """Return set of required host ports (aka non auto ports) from
        site_list.

        Returns: set of integers

        Expected format for ports:
        port = {
            "80":{
                "name": web,
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
                print_red("Error: for site config:", e)
                print(pformat(site))
                raise
        return used

    def generate_ports_for_sites(self, allocator: Callable):
        """Update site dict with auto generated ports."""
        for site in self.sites:
            site.allocate_auto_ports(allocator)
            for resource in site.resources:
                resource.allocate_auto_ports(allocator)

    def update_ports_from_nua_config(self):
        """If port not declared in site config, use image definition.

        Merge ports modifications from site config with image config.
        """
        if verbosity(5):
            print(f"update_ports_from_nua_config(): len(site_list)= {len(self.sites)}")
        for site in self.sites:
            site.rebase_ports_upon_nua_config()

    def set_container_names(self, site: Site):
        """Set first container names of resources to permit early host
        assignment to variables.

        Site.container_name is always available)
        """
        for resource in site.resources:
            if resource.type == "docker":
                name = f"{site.container_name}-{resource.base_name}"
                # - code will be rename to container_name
                # - See if we tryst Docker to overwrite this variable
                #   (or emit a warning if pb)
                resource.container = name

    def evaluate_container_params(self, site: Site):
        """Compute site run envronment parameters except those requiring late
        evaluation (i.e. host names of started containers).

        Order of evaluations for Variables:
        - main Site variable assignment (including hostname of resources)
        - Resource assignement (they have access to site ENV)
        - late evaluation (hostnames)
        """
        self.generate_site_container_run_parameters(site)
        env = site.run_params["environment"]
        for resource in site.resources:
            if resource.type == "docker":
                self.generate_resource_container_run_parameters(site, resource, env)

    def retrieve_persistent(self, site: Site):
        previous = store.instance_persistent(site.domain, site.app_id)
        if verbosity(4):
            print(f"persistent previous: {previous=}")
        previous.update(site.persistent)
        site.persistent = previous

    def start_network(self, site: Site):
        if site.network_name:
            create_container_private_network(site.network_name)

    def start_resources_containers(self, site: Site):
        for resource in site.resources:
            if resource.type == "docker":
                mounted_volumes = mount_resource_volumes(resource)
                start_one_container(resource, mounted_volumes)
                # until we check startup of container or set value in parameters...
                time.sleep(2)

    def start_main_site_container(self, site: Site):
        # volumes need to be mounted before beeing passed as arguments to
        # docker.run()
        mounted_volumes = mount_resource_volumes(site)
        start_one_container(site, mounted_volumes)

    def store_container_instance(self, site: Site):
        if verbosity(2):
            print("saving site config in Nua DB")
        meta = site.image_nua_config["metadata"]
        store.store_instance(
            app_id=site.app_id,
            nua_tag=store.nua_tag_string(meta),
            domain=site.domain,
            container=site.container,
            image=site.image,
            state=RUNNING,
            site_config=dict(site),
        )

    def generate_site_container_run_parameters(self, site: Site):
        """Return suitable parameters for the docker.run() command.

        Does not include the internal_secrets, that are passed only at
        docker.run() execution, thus secrets not stored in instance
        data.
        """
        # base defaults hardcoded and from nua orchestrator configuration
        run_params = deepcopy(RUN_BASE)
        nua_docker_default_run = config.read("nua", "docker_default_run") or {}
        run_params.update(nua_docker_default_run)
        # run parameters defined in the image configuration, without the "env"
        # sections:
        run_nua_conf = deepcopy(site.image_nua_config.get("run", {}))
        if "env" in run_nua_conf:
            del run_nua_conf["env"]
        run_params.update(run_nua_conf)
        # update with parameters that could be added to Site configuration :
        run_params.update(site.get("run", {}))
        # Add the hostname/IP of local Docker hub (Docker feature) :
        self.add_host_gateway_to_extra_hosts(run_params)
        run_params["name"] = site.container_name
        run_params["ports"] = site.ports_as_docker_params()
        run_params["environment"] = self.run_parameters_environment(site)
        if site.healthcheck:
            run_params["healthcheck"] = HealthCheck(site.healthcheck).as_docker_params()
        self.sanitize_run_params(run_params)
        site.run_params = run_params

    def generate_resource_container_run_parameters(
        self, site: Site, resource: Resource, site_env: dict
    ):
        """Return suitable parameters for the docker.run() command (for
        Resource)."""
        run_params = deepcopy(RUN_BASE_RESOURCE)
        run_params.update(resource.get("run", {}))
        self.add_host_gateway_to_extra_hosts(run_params)
        run_params["name"] = f"{site.container_name}-{resource.base_name}"
        run_params["ports"] = resource.ports_as_docker_params()
        run_params["environment"] = self.run_parameters_resource_environment(
            resource, site_env
        )
        if resource.healthcheck:
            run_params["healthcheck"] = HealthCheck(
                resource.healthcheck
            ).as_docker_params()
        self.sanitize_run_params(run_params)
        resource.run_params = run_params

    @staticmethod
    def add_host_gateway_to_extra_hosts(run_params: dict):
        extra_hosts = run_params.get("extra_hosts", {})
        extra_hosts.update(extra_host_gateway())
        run_params["extra_hosts"] = extra_hosts

    def run_parameters_environment(self, site: Site) -> dict:
        """Return a dict with all environment parameters for the main container
        to run (the Site container)."""
        run_env = site.image_nua_config.get("run_env", {})  # deprecated syntax
        # first the run.env section of nua config file:
        run_env.update(site.image_nua_config.get("run", {}).get("env", {}))
        # update with local services environment (if any):
        run_env.update(self.services_environment(site))
        # update with result of "assign" dynamic evaluations :
        run_env.update(instance_key_evaluator(site, late_evaluation=False))
        # variables declared in the run.env section of the ochestrator deployment
        # configurationcan replace any other source:
        run_env.update(site.run_env)
        return run_env

    def run_parameters_resource_environment(
        self, resource: Resource, site_env: dict
    ) -> dict:
        """Return a dict with all environment parameters for a resource
        container (a Resource container)."""
        # resource has access to environment of main container:
        run_env = deepcopy(site_env)
        # update with result of "assign" dynamic evaluations :
        run_env.update(instance_key_evaluator(resource, late_evaluation=False))
        # variables declared in run.env can replace any other source:
        run_env.update(resource.run_env)
        resource.run_env = run_env
        return run_env

    @staticmethod
    def sanitize_run_params(run_params: dict):
        """Docker constraint: 2 docker options not compatible."""
        if "restart_policy" in run_params:
            run_params["auto_remove"] = False

    def services_environment(self, site: Site) -> dict:
        run_env = {}
        for service in site.local_services:
            handler = self.available_services[service]
            # function may need or not site param:
            run_env.update(handler.environment(site))
        return run_env

    def resources_environment(self, site: Site) -> dict:
        run_env = {}
        for resource in site.resources:
            run_env.update(resource.environment_ports())
        return run_env

    def post_deployment(self):
        self.store_deploy_configs_after_swap()
        self.display_final()

    def display_final(self):
        self.display_deployed()
        self.display_used_volumes()
        self.display_unused_volumes()

    def display_deployed(self):
        protocol = protocol_prefix()
        for site in self.sites:
            msg = f"image '{site.image}' deployed as {protocol}{site.domain}"
            info(msg)
            self.display_persistent_data(site)

    def display_persistent_data(self, site: Site):
        if verbosity(1) and site.persistent:
            print_green("Persistent generated variables:")
            for key, val in site.persistent.items():
                info(f"    {key}: {val}")

    def display_used_volumes(self):
        if not verbosity(1):
            return
        current_mounted = store.list_instances_container_active_volumes()
        if not current_mounted:
            return
        print_green("Volumes used by current Nua configuration:")
        for volume in current_mounted:
            print(Volume.string(volume))

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
            print(Volume.string(volume))

    def print_host_list(self):
        print("sites per domain:\n", pformat(self.sites_per_domain))


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
    valid_sites = []
    hostname = host["hostname"]
    for site in host["sites"]:
        dom = DomainSplit(site.domain)
        if not dom.location:
            image = site.image
            warning(
                "required location is missing, site discarded:",
                f"for {hostname=} / {image=}",
            )
            continue
        if dom.location in known_location:
            image = site.image
            # port = site.get("port")
            warning(
                "location is already used for a domain, site discarded:",
                f"{hostname=} / {image=} / {site.domain}",
            )
            continue
        known_location.add(dom.location)
        site["location"] = dom.location
        valid_sites.append(site)
    host["sites"] = valid_sites
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
        valid_sites = host["sites"]
    else:
        hostname = host["hostname"]
        warning(f"too many sites for {hostname=}, site discarded:")
        site = host["sites"].pop(0)
        valid_sites = [site]
        for site in host["sites"]:
            image = site.image
            print_red(f"    {image=} / {site['domain']}")

    host["sites"] = valid_sites
    host["located"] = False
