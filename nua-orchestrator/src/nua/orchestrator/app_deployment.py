"""Class to manage the deployment of a group of app instances."""
import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from typing import Any

from nua.lib.console import print_green, print_red
from nua.lib.panic import abort, info, vprint, vprint_green, vprint_magenta, warning
from nua.lib.tool.state import verbosity

from . import config
from .app_instance import AppInstance
from .assign.engine import instance_key_evaluator
from .certbot import protocol_prefix, register_certbot_domains
from .db import store
from .db.model.deployconfig import ACTIVE, INACTIVE, PREVIOUS
from .db.model.instance import RUNNING
from .deploy_utils import (
    create_container_private_network,
    deactivate_all_instances,
    deactivate_app,
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
from .resource import Resource
from .services import Services
from .utils import parse_any_format
from .volume import Volume

# parameters passed as a dict to docker run
RUN_BASE: dict[str, Any] = {}  # see also nua_config
RUN_BASE_RESOURCE = {"restart_policy": {"name": "always"}}


class AppDeployment:
    """Deployment of a list of app instance/nua-image.

    Devel notes: will be refactored into base class and sub classes for various
    deployment strategies (restoring previous configuration, ...).

    example of use:
        deployer = AppDeployment()
        deployer.local_services_inventory()
        deployer.load_deploy_config(deploy_config)
        deployer.gather_requirements()
        deployer.configure_apps()
        deployer.deactivate_previous_apps()
        deployer.apply_configuration()
        deployer.start_apps()
        deployer.post_deployment()
    """

    def __init__(self):
        self.loaded_config = {}
        self.apps = []
        self.apps_per_domain = []
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
        #     "apps": deepcopy(self.apps),
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
            "apps": deepcopy(self.apps),
        }
        self.future_config_id = store.deploy_config_add_config(
            deploy_config, self.previous_config_id, ACTIVE
        )

    def local_services_inventory(self):
        """Initialization step: inventory of available resources available on
        the host, like local databases."""
        # See later
        return
        # assuming nua_db_setup was run at initialization of the command
        services = Services()
        services.load()
        self.available_services = services.loaded
        with verbosity(2):
            vprint_magenta(
                f"Available local services: {pformat(list(services.loaded.keys()))}"
            )

    def load_deploy_config(self, deploy_config: str):
        config_path = Path(deploy_config).expanduser().resolve()
        with verbosity(1):
            info(f"Deploy apps from: {config_path}")
        self.loaded_config = parse_any_format(config_path)
        self.parse_deploy_apps()
        self.sort_apps_per_domain()
        with verbosity(3):
            self.print_host_list()

    def restore_previous_deploy_config_strict(self):
        """Retrieve last successful deployment configuration (strict mode)."""
        with verbosity(1):
            info("Deploy apps from previous deployment (strict mode).")
        previous_config = self.previous_success_deployment_record()
        if not previous_config:
            abort("Impossible to find a previous deployment.")
        self.loaded_config = previous_config["deployed"]["requested"]
        self.apps = []
        for site_dict in previous_config["deployed"]["apps"]:
            self.apps.append(AppInstance.from_dict(site_dict))
        # self.future_config_id = previous_config.get("id")
        self.sort_apps_per_domain()

    def restore_previous_deploy_config_replay(self):
        """Retrieve last successful deployment configuration (replay mode)."""
        with verbosity(1):
            info("Deploy apps from previous deployment (replay deployment).")
        previous_config = self.previous_success_deployment_record()
        if not previous_config:
            abort("Impossible to find a previous deployment.")
        self.loaded_config = previous_config["deployed"]["requested"]
        # self.future_config_id = previous_config.get("id")
        self.parse_deploy_apps()
        self.sort_apps_per_domain()
        with verbosity(3):
            self.print_host_list()

    def gather_requirements(self):
        self.install_required_images()
        self.install_required_resources()

    def configure_apps(self):
        self.apps_set_network_name()
        self.apps_set_resources_names()
        self.apps_merge_instances_to_resources()
        self.apps_configure_requested_db()
        self.apps_set_volumes_names()
        self.apps_check_local_service_available()
        self.apps_set_ports_as_dict()
        self.apps_parse_healthcheck()
        self.apps_check_host_services_configuration()
        self.apps_retrieve_persistent()
        # We now allocate ports *before* stopping services, thus this may induce
        # a flip/flop balance when reinstalling same config
        self.apps_generate_ports()

    def restore_configure(self):
        """Try to reuse the previous configuration with no change."""
        self.apps_check_local_service_available()
        self.apps_check_host_services_configuration()

    def deactivate_previous_apps(self):
        """Find all instance in DB.

        - remove container if exists
        - remove site from Nua DB
        """
        self.store_deploy_configs_before_swap()
        self.orig_mounted_volumes = store.list_instances_container_active_volumes()
        deactivate_all_instances()

    def restore_deactivate_previous_apps(self):
        """For restore situation, find all instance in DB.

        - remove container if exists
        - remove site from Nua DB
        """
        self.orig_mounted_volumes = store.list_instances_container_active_volumes()
        deactivate_all_instances()

    def apply_configuration(self):
        """Apply configuration, especially configurations that can not be
        deployed before all previous apps are stopped."""
        self.configure_nginx()
        # registering https apps with certbot requires that the base nginx config is
        # deployed.
        register_certbot_domains(self.apps)
        with verbosity(2):
            vprint("'apps':\n", pformat(self.apps))

    def start_apps(self):
        """Start all apps to deploy."""
        # restarting local services:
        self.restart_local_services()
        for site in self.apps:
            deactivate_app(site)
            self.start_network(site)
            self.evaluate_container_params(site)
            self.start_resources_containers(site)
            self.setup_resources_db(site)
            self.merge_volume_only_resources(site)
            self.start_main_app_container(site)
            self.store_container_instance(site)
        chown_r_nua_nginx()
        nginx_restart()

    def parse_deploy_apps(self):
        """Make the list of AppInstances.

        Check config syntax, replace missing information by defaults.
        """
        apps = []
        for site_dict in self.loaded_config["site"]:
            if not isinstance(site_dict, dict):
                abort(
                    "AppInstance configuration must be a dict",
                    explanation=f"{pformat(site_dict)}",
                )
            site = AppInstance(site_dict)
            site.check_valid()
            # site.set_ports_as_dict()
            apps.append(site)
        self.apps = apps

    def sort_apps_per_domain(self):
        """Classify the apps per domain, filtering out miss declared apps.

        The apps per domain are available in self.apps_per_domain
        """
        self._make_apps_per_domain()
        self._filter_miss_located_apps()
        self._update_apps_list()

    def _make_apps_per_domain(self):
        """Convert dict(hostname:[apps,..]) to list({hostname, apps}).

        ouput format:
        [{'hostname': 'test.example.com',
         'apps': [{'domain': 'test.example.com/instance1',
                     'image': 'flask-one:1.2-1',
                     },
                    {'domain': 'test.example.com/instance2',
                     'image': 'flask-one:1.2-1',
                     },
                     ...
         {'hostname': 'sloop.example.com',
          'apps': [{'domain': 'sloop.example.com',
                     'image': 'nua-flask-upload-one:1.0-1',
                     }]}]
        """
        apps_per_domain = self._apps_per_domain()
        self.apps_per_domain = [
            {"hostname": hostname, "apps": apps_list}
            for hostname, apps_list in apps_per_domain.items()
        ]

    def _apps_per_domain(self) -> dict:
        """Return a dict of apps per host.

        key : hostname (full name)
        value : list of webapps of hostname

        input format: dict contains a list of apps

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
        apps_per_domain = {}
        for site in self.apps:
            dom = DomainSplit(site.domain)
            if dom.hostname not in apps_per_domain:
                apps_per_domain[dom.hostname] = []
            apps_per_domain[dom.hostname].append(site)
        return apps_per_domain

    def _filter_miss_located_apps(self):
        """Return apps classified for location use.

        For a domain:
            - either only one site:
                www.example.com -> site
            - either all apps must have a location (path):
                www.example.com/path1 -> site1
                www.example.com/path2 -> site2

        So, if not located, check it is the only one site of the domain.
        The method checks the coherence and add a located 'flag'
        """
        for host in self.apps_per_domain:
            apps_list = host["apps"]
            first = apps_list[0]  # by construction, there is at least 1 element
            dom = DomainSplit(first.domain)
            if dom.location:
                _verify_located(host)
            else:
                _verify_not_located(host)

    def _update_apps_list(self):
        """Rebuild the list of AppInstance from filtered apps per domain."""
        apps_list = []
        for host in self.apps_per_domain:
            for site in host["apps"]:
                site.hostname = host["hostname"]
                apps_list.append(site)
        self.apps = apps_list

    def install_required_images(self):
        # first: check that all Nua images are available:
        if not self.find_all_apps_images():
            abort("Missing Nua images")
        self.install_images()

    def find_all_apps_images(self) -> bool:
        for site in self.apps:
            if not site.find_registry_path():
                print_red(f"No image found for '{site.image}'")
                return False
        with verbosity(1):
            seen = set()
            for site in self.apps:
                if site.image not in seen:
                    seen.add(site.image)
                    info(f"Image found: '{site.image}'")
        return True

    def install_images(self):
        start_container_engine()
        installed = {}
        for site in self.apps:
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
        self.apps_parse_resources()
        self.apps_set_ports_as_dict()
        if not self.pull_all_resources_images():
            abort("Missing Docker images")

    def pull_all_resources_images(self) -> bool:
        return all(
            all(self._pull_resource(resource) for resource in site.resources)
            for site in self.apps
        )

    def _pull_resource(self, resource: Resource) -> bool:
        if resource.type == "local":
            # will check later in the process
            return True
        if resource.is_docker_type():
            with verbosity(4):
                vprint("pull docker resource:", resource)
            return pull_resource_container(resource)
        return True

    def apps_check_local_service_available(self):
        self.required_services = {s for site in self.apps for s in site.local_services}
        with verbosity(3):
            vprint("required services:", self.required_services)
        available_services = set(self.available_services.keys())
        for service in self.required_services:
            if service not in available_services:
                abort(f"Required service '{service}' is not available")

    def apps_check_host_services_configuration(self):
        for site in self.apps:
            for service in site.local_services:
                handler = self.available_services[service]
                if not handler.check_site_configuration(site):
                    abort(
                        f"Required service '{service}' not configured for "
                        f"site {site.domain}"
                    )

    def apps_parse_resources(self):
        for site in self.apps:
            site.parse_resources()

    def apps_set_ports_as_dict(self):
        for site in self.apps:
            site.set_ports_as_dict()

    def apps_parse_healthcheck(self):
        for site in self.apps:
            site.parse_healthcheck()
        with verbosity(3):
            info("apps_parse_healthcheck() done")

    def apps_set_network_name(self):
        for site in self.apps:
            site.set_network_name()
        with verbosity(3):
            info("apps_set_network_name() done")

    def apps_set_resources_names(self):
        for site in self.apps:
            site.set_resources_names()
        with verbosity(3):
            info("apps_set_resources_names() done")

    def apps_merge_instances_to_resources(self):
        for site in self.apps:
            site.merge_instance_to_resources()
        with verbosity(3):
            info("apps_merge_instances_to_resources() done")

    def apps_configure_requested_db(self):
        for site in self.apps:
            for resource in site.resources:
                resource.configure_db()
        with verbosity(3):
            info("apps_configure_requested_db() done")

    def apps_set_volumes_names(self):
        for site in self.apps:
            site.set_volumes_names()
        with verbosity(3):
            info("apps_set_volumes_names() done")

    def restart_local_services(self):
        with verbosity(2):
            if self.required_services:
                info("Services to restart:", pformat(self.required_services))
            else:
                info("Services to restart: None")
        for service in self.required_services:
            handler = self.available_services[service]
            handler.restart()

    def configure_nginx(self):
        clean_nua_nginx_default_site()
        for host in self.apps_per_domain:
            with verbosity(1):
                info(f"Configure Nginx for hostname '{host['hostname']}'")
            configure_nginx_hostname(host)

    def apps_generate_ports(self):
        start_ports = config.read("nua", "ports", "start") or 8100
        end_ports = config.read("nua", "ports", "end") or 9000
        with verbosity(4):
            vprint(f"apps_generate_ports(): interval {start_ports} to {end_ports}")
        self.update_ports_from_nua_config()
        allocated_ports = self._configured_ports()
        with verbosity(4):
            vprint(f"apps_generate_ports(): {allocated_ports=}")
        # list of ports used for domains / apps, trying to keep them unchanged
        ports_instances_domains = store.ports_instances_domains()
        with verbosity(4):
            vprint(f"apps_generate_ports(): {ports_instances_domains=}")
        allocated_ports.update(ports_instances_domains)
        with verbosity(3):
            vprint(f"apps_generate_ports() used ports:\n {allocated_ports=}")
        self.apps_allocate_ports(
            port_allocator(start_ports, end_ports, allocated_ports)
        )
        with verbosity(3):
            vprint("apps_generate_ports() done")

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
        for site in self.apps:
            try:
                used.update(site.used_ports())
            except (ValueError, IndexError) as e:
                print_red("Error: for site config:", e)
                print(pformat(site))
                raise
        return used

    def apps_allocate_ports(self, allocator: Callable):
        """Update site dict with auto generated ports."""
        for site in self.apps:
            site.allocate_auto_ports(allocator)
            for resource in site.resources:
                resource.allocate_auto_ports(allocator)

    def update_ports_from_nua_config(self):
        """If port not declared in site config, use image definition.

        Merge ports modifications from site config with image config.
        """
        with verbosity(5):
            vprint(f"update_ports_from_nua_config(): len(site_list)= {len(self.apps)}")
        for site in self.apps:
            site.rebase_ports_upon_nua_config()

    def evaluate_container_params(self, site: AppInstance):
        """Compute site run envronment parameters except those requiring late
        evaluation (i.e. host names of started containers).

        Order of evaluations for Variables:
        - main AppInstance variable assignment (including hostname of resources)
        - Resource assignement (they have access to site ENV)
        - late evaluation (hostnames)
        """
        env = {}
        for resource in site.resources:
            if (not resource.is_assignable()) or (
                resource.is_assignable()
                and resource.assign_priority < site.assign_priority
            ):
                self.generate_resource_container_run_parameters(site, resource, env)
        self.generate_app_container_run_parameters(site)
        env = site.run_params["environment"]
        for resource in site.resources:
            if (
                resource.is_assignable()
                and resource.assign_priority >= site.assign_priority
            ):
                self.generate_resource_container_run_parameters(site, resource, env)

    def apps_retrieve_persistent(self):
        for site in self.apps:
            self.retrieve_persistent(site)

    def retrieve_persistent(self, site: AppInstance):
        previous = store.instance_persistent(site.domain, site.app_id)
        with verbosity(4):
            vprint(f"persistent previous: {previous=}")
        previous.update(site.persistent_full_dict())
        site.set_persistent_full_dict(previous)

    def start_network(self, site: AppInstance):
        if site.network_name:
            create_container_private_network(site.network_name)

    def start_resources_containers(self, site: AppInstance):
        for resource in site.resources:
            if resource.is_docker_type():
                mounted_volumes = mount_resource_volumes(resource)
                start_one_container(resource, mounted_volumes)
                # until we check startup of container or set value in parameters...
                time.sleep(2)

    def setup_resources_db(self, site: AppInstance):
        for resource in site.resources:
            resource.setup_db()

    def merge_volume_only_resources(self, site: AppInstance):
        for resource in site.resources:
            if resource.volume_declaration:
                site.volume = site.volume + resource.volume_declaration

    def start_main_app_container(self, site: AppInstance):
        # volumes need to be mounted before beeing passed as arguments to
        # docker.run()
        mounted_volumes = mount_resource_volumes(site)
        start_one_container(site, mounted_volumes)

    def store_container_instance(self, site: AppInstance):
        with verbosity(2):
            vprint("saving site config in Nua DB")
        store.store_instance(
            app_id=site.app_id,
            nua_tag=site.nua_tag,
            domain=site.domain,
            container=site.container_name,
            image=site.image,
            state=RUNNING,
            site_config=dict(site),
        )

    def generate_app_container_run_parameters(self, site: AppInstance):
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
        run_nua_conf = deepcopy(site.image_nua_config.get("docker", {}))
        if "env" in run_nua_conf:
            del run_nua_conf["env"]
        run_params.update(run_nua_conf)
        # update with parameters that could be added to AppInstance configuration :
        run_params.update(site.get("docker", {}))
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
        self, site: AppInstance, resource: Resource, site_env: dict
    ):
        """Return suitable parameters for the docker.run() command (for
        Resource)."""
        run_params = deepcopy(RUN_BASE_RESOURCE)
        run_params.update(resource.docker)
        self.add_host_gateway_to_extra_hosts(run_params)
        run_params["name"] = resource.container_name
        run_params["ports"] = resource.ports_as_docker_params()
        run_params["environment"] = self.run_parameters_resource_environment(
            site, resource, site_env
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

    def run_parameters_environment(self, site: AppInstance) -> dict:
        """Return a dict with all environment parameters for the main container
        to run (the AppInstance container)."""
        run_env = site.image_nua_config.get("env", {})
        # update with local services environment (if any):
        run_env.update(self.services_environment(site))
        # update with result of "assign" dynamic evaluations :
        run_env.update(instance_key_evaluator(site, late_evaluation=False))
        # variables declared in the env section of the ochestrator deployment
        # configurationcan replace any other source:
        run_env.update(site.env)
        return run_env

    def run_parameters_resource_environment(
        self, site: AppInstance, resource: Resource, site_env: dict
    ) -> dict:
        """Return a dict with all environment parameters for a resource
        container (a Resource container)."""
        # resource has access to environment of main container:
        run_env = deepcopy(site_env)
        # update with result of "assign" dynamic evaluations :
        run_env.update(
            instance_key_evaluator(site, resource=resource, late_evaluation=False)
        )
        # variables declared in env can replace any other source:
        run_env.update(resource.env)
        resource.env = run_env
        return run_env

    @staticmethod
    def sanitize_run_params(run_params: dict):
        """Docker constraint: 2 docker options not compatible."""
        if "restart_policy" in run_params:
            run_params["auto_remove"] = False

    def services_environment(self, site: AppInstance) -> dict:
        run_env = {}
        for service in site.local_services:
            handler = self.available_services[service]
            # function may need or not site param:
            run_env.update(handler.environment(site))
        return run_env

    def resources_environment(self, site: AppInstance) -> dict:
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
        for site in self.apps:
            msg = f"image '{site.image}' deployed as {protocol}{site.domain}"
            info(msg)
            self.display_persistent_data(site)

    def display_persistent_data(self, site: AppInstance):
        with verbosity(3):
            content = site.persistent_full_dict()
            if content:
                vprint_green("Persistent generated variables:")
                vprint(pformat(content))

    def display_used_volumes(self):
        with verbosity(1):
            current_mounted = store.list_instances_container_active_volumes()
            if not current_mounted:
                return
            vprint_green("Volumes used by current Nua configuration:")
            for volume in current_mounted:
                vprint(Volume.string(volume))

    def display_unused_volumes(self):
        with verbosity(1):
            unused = unused_volumes(self.orig_mounted_volumes)
            if not unused:
                return
            print_green(
                "Some volumes are mounted but not used by current Nua configuration:"
            )
            for volume in unused:
                vprint(Volume.string(volume))

    def print_host_list(self):
        vprint("apps per domain:\n", pformat(self.apps_per_domain))


def _verify_located(host: dict):
    """host format:

     {'hostname': 'test.example.com',
      'apps': [{'domain': 'test.example.com/instance1',
                  'image': 'flask-one:1.2-1',
                  # 'port': 'auto',
                  },
                 {'domain': 'test.example.com/instance2',
                  'image': 'flask-one:1.2-1',
                  ...
    changed to:
    {'hostname': 'test.example.com',
     'located': True,
     'apps': [{'domain': 'test.example.com/instance1',
                 'image': 'flask-one:1.2-1',
                 # 'port': 'auto',
                 'location': 'instance1'
                 },
                {'domain': 'test.example.com/instance2',
                 'image': 'flask-one:1.2-1',
                 ...
    """
    known_location = set()
    valid_apps = []
    hostname = host["hostname"]
    for site in host["apps"]:
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
        valid_apps.append(site)
    host["apps"] = valid_apps
    host["located"] = True


def _verify_not_located(host: dict):
    """host format:

        {'hostname': 'sloop.example.com',
         'apps': [{'domain': 'sloop.example.com',
                    'image': 'nua-flask-upload-one:1.0-1',
                    'port': 'auto'}]}]
    changed to:
        {'hostname': 'sloop.example.com',
         'located': False,
         'apps': [{'domain': 'sloop.example.com',
                    'image': 'nua-flask-upload-one:1.0-1',
                    'port': 'auto'}]}]
    """
    # we know that the first of the list is not located. We expect the list
    # has only one site.
    if len(host["apps"]) == 1:
        valid_apps = host["apps"]
    else:
        hostname = host["hostname"]
        warning(f"too many apps for {hostname=}, site discarded:")
        site = host["apps"].pop(0)
        valid_apps = [site]
        for site in host["apps"]:
            image = site.image
            print_red(f"    {image=} / {site['domain']}")

    host["apps"] = valid_apps
    host["located"] = False
