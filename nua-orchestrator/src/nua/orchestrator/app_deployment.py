"""Class to manage the deployment of a group of app instances.

Note:
    - Security of deployment (deploy an app instance upon an existing one) is not
      currently managed in this level.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from typing import Any

from nua.lib.panic import (
    Abort,
    bold_debug,
    debug,
    important,
    info,
    red_line,
    show,
    vprint,
    warning,
)
from nua.lib.tool.state import verbosity

from . import config
from .app_instance import AppInstance
from .assign.engine import instance_key_evaluator
from .certbot import protocol_prefix, register_certbot_domains
from .db import store
from .db.model.deployconfig import ACTIVE, INACTIVE, PREVIOUS
from .db.model.instance import RUNNING, STOPPED
from .deploy_utils import (
    create_container_private_network,
    deactivate_all_instances,
    deactivate_app,
    extra_host_gateway,
    load_install_image,
    mount_resource_volumes,
    port_allocator,
    pull_resource_container,
    remove_container_private_network,
    remove_volume_by_source,
    restart_one_app_containers,
    start_container_engine,
    start_one_app_containers,
    start_one_container,
    stop_one_app_containers,
    unused_volumes,
)
from .domain_split import DomainSplit
from .healthcheck import HealthCheck
from .nginx.cmd import nginx_reload, nginx_restart
from .nginx.utils import (
    chown_r_nua_nginx,
    clean_nua_nginx_default_site,
    configure_nginx_hostname,
    remove_nginx_configuration_hostname,
)
from .resource import Resource
from .services import Services
from .utils import parse_any_format
from .volume import Volume

# parameters passed as a dict to docker run
RUN_BASE: dict[str, Any] = {}  # see also nua_config
RUN_BASE_RESOURCE = {"restart_policy": {"name": "always"}}


def known_strings(current: list[str], new: list[str]) -> list[str]:
    return [s for s in new if s in set(current)]


class AppDeployment:
    """Deployment of a list of app instance/nua-image.

    Devel notes: will be refactored into base class and subclasses for various
    deployment strategies (restoring previous configuration, ...).

    example of use:
        deployer = AppDeployment()
        deployer.local_services_inventory()
        deployer.load_deploy_config(deploy_config)
        deployer.gather_requirements()
        deployer.configure_apps()
        deployer.deactivate_previous_apps()
        deployer.apply_nginx_configuration()
        deployer.start_apps()
        deployer.post_deployment()
    """

    def __init__(self):
        self.loaded_config = {}
        self.apps = []
        self.apps_per_domain = []
        self.deployed_domains = []
        self.already_deployed_domains = set()
        self.deployed_labels = []
        self.already_deployed_labels = set()
        self.required_services = set()
        self.available_services = {}
        self.orig_mounted_volumes = []
        self.previous_config_id = 0
        self._mounted_before_removing = []  # internal use when removing app instance
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

    def remove_app_instance(self, removed_app: AppInstance):
        label_id = removed_app.label_id
        apps = [app for app in self.apps if app.label_id != label_id]
        self.apps = apps
        self.sort_apps_per_name_domain()
        self.remove_domain_from_config(removed_app.domain)

    def remove_domain_from_config(self, domain: str):
        apps = self.loaded_config.get("site", [])
        filtered = [app for app in apps if app.get("domain", "") != domain]
        self.loaded_config["site"] = filtered

    def local_services_inventory(self):
        """Initialization step: inventory of available resources available on
        the host, like local databases."""
        # See later
        return
        # assuming nua_db_setup was run at initialization of the command
        services = Services()
        services.load()
        self.available_services = services.loaded
        with verbosity(1):
            bold_debug(
                f"Available local services: {pformat(list(services.loaded.keys()))}"
            )

    def load_deploy_config(self, deploy_config: str):
        config_path = Path(deploy_config).expanduser().resolve()
        with verbosity(0):
            info(f"Deploy apps from: {config_path}")
        self.loaded_config = parse_any_format(config_path)
        self.parse_deploy_apps()
        self.sort_apps_per_name_domain()
        self.deployed_domains = sorted(
            {apps["hostname"] for apps in self.apps_per_domain}
        )
        self.deployed_labels = sorted(app.label_id for app in self.apps)
        with verbosity(3):
            self.print_host_list()

    def load_deployed_configuration(self):
        previous_config = self.previous_success_deployment_record()
        if not previous_config:
            with verbosity(1):
                show("First deployment (no previous deployed configuration found)")
            self.loaded_config = {}
            self.apps = []
            self.deployed_domains = []
            return
        self.loaded_config = previous_config["deployed"]["requested"]
        self.apps = [
            AppInstance.from_dict(app_instance_data)
            for app_instance_data in previous_config["deployed"]["apps"]
        ]
        self.sort_apps_per_name_domain()
        self.deployed_domains = sorted(
            {apps_dom["hostname"] for apps_dom in self.apps_per_domain}
        )

    def merge(self, additional: AppDeployment, option: str = "add"):
        """Merge a deployment configuration into the current deployed configuration.

        WIP:
            - first step: 'add', strict, no conflict allowed
            - next: add and replace if needed (merge)
        """
        with verbosity(3):
            debug(f"Deployment merge option: {option}")
        if option == "add":
            return self.merge_add(additional)
        raise RuntimeError("Merge option not implemented")

    def merge_sequential(self, additional: AppDeployment):
        """Merge a deployment configuration sequentially."""
        with verbosity(3):
            debug("Deployment merge sequentially")
        for app in additional.apps:
            deploy_strategy = self.evaluate_deploy_strategy(app)
            method = getattr(self, deploy_strategy)
            method(app)

    def evaluate_deploy_strategy(self, merged_app: AppInstance) -> str:
        same_label_app = next(
            (app for app in self.apps if app.label_id == merged_app.label_id), None
        )
        same_domain_app = next(
            (app for app in self.apps if app.domain == merged_app.domain), None
        )
        if same_label_app:
            return self._deploy_same_label_strategy(
                merged_app,
                same_label_app,
                same_domain_app,
            )
        else:
            if same_domain_app:
                raise Abort(
                    f"Domain '{merged_app.domain}' already in use "
                    f"for another label: {same_domain_app.label}"
                )
            # new label on new domain
            return "deploy_new_app"

    def _deploy_same_label_strategy(
        self,
        merged_app: AppInstance,
        same_label_app: AppInstance,
        same_domain_app: AppInstance,
    ) -> str:
        if same_label_app.domain == merged_app.domain:
            if same_label_app.app_id == merged_app.app_id:
                # same app on on same domain
                return "deploy_update_app"
            else:
                # another app on same domain
                return "deploy_replace_app"
        else:
            if merged_app.domain in self.deployed_domains:
                # but not our domain
                raise Abort(
                    f"Domain '{merged_app.domain}' already in use "
                    f"for another label: {same_domain_app.label}"
                )
            else:
                if same_label_app.app_id == merged_app.app_id:
                    # same app on another domain
                    return "deploy_move_domain"
                else:
                    # another app on another domain
                    return "deploy_reuse_label"

    def deploy_new_app(self, app: AppInstance):
        """Deploy new label and app on new domain."""
        important(f"Deploy '{app.label}': a new {app.app_id} on '{app.domain}'")
        self._deploy_new_app(app)

    def _deploy_new_app(
        self,
        app: AppInstance,
        persistent: dict | None = None,
    ):
        """Deploy an app."""
        # step 1:
        app.set_network_name()
        app.set_resources_names()
        app.merge_instance_to_resources()
        for resource in app.resources:
            resource.configure_db()
        app.set_volumes_names()
        for service in app.local_services:
            if service not in self.available_services:
                raise Abort(f"Required service '{service}' is not available")
        if persistent:
            with verbosity(2):
                debug(pformat(persistent))
            # if really new app, not persistent for now, but some persitent data if
            # reusing same label_id for a new app: then try to retrieve the persistent
            # data of previous Appinstance:
            app.set_persistent_full_dict(persistent)
        self.evaluate_dynamic_values(app)

        # step 2: ports
        start_ports = config.read("nua", "ports", "start") or 8100
        end_ports = config.read("nua", "ports", "end") or 9000
        allocated_ports = self.configured_ports()
        ports_instances_domains = store.ports_instances_domains()
        allocated_ports.update(ports_instances_domains)
        allocator = port_allocator(start_ports, end_ports, allocated_ports)
        app.allocate_auto_ports(allocator)
        for resource in app.resources:
            resource.allocate_auto_ports(allocator)

        # step 3
        app.parse_healthcheck()
        for service in app.local_services:
            handler = self.available_services[service]
            if not handler.check_site_configuration(app):
                raise Abort(
                    f"Required service '{service}' not configured for "
                    f"app {app.domain}"
                )
        self.store_initial_deployment_state()
        self.already_deployed_domains = set(self.deployed_domains)
        self.already_deployed_labels = set(self.deployed_labels)
        self.apps.append(app)
        self.sort_apps_per_name_domain()
        self.merge_nginx_configuration()
        self.deployed_domains = sorted(
            {apps_dom["hostname"] for apps_dom in self.apps_per_domain}
        )
        self.deployed_labels = sorted(a.label_id for a in self.apps)
        self._start_apps([app], deactivate=False)

    def deploy_update_app(self, merged_app: AppInstance):
        """Deploy same app on on same domain."""
        important(
            f"Deploy '{merged_app.label}': update {merged_app.app_id} "
            f"on '{merged_app.domain}'"
        )
        same_label_app = next(
            (app for app in self.apps if app.label_id == merged_app.label_id), None
        )
        persistent_data = same_label_app.persistent_full_dict()
        self._remove_per_label(same_label_app, remove_volumes=False)
        self._deploy_new_app(merged_app, persistent=persistent_data)

    def deploy_replace_app(self, merged_app: AppInstance):
        """Deploy another app on same domain."""
        same_label_app = next(
            (app for app in self.apps if app.label_id == merged_app.label_id), None
        )
        important(
            f"Deploy '{merged_app.label}': replace {same_label_app.app_id} "
            f"by {merged_app.app_id} on '{merged_app.domain}'"
        )
        self._remove_per_label(merged_app, remove_volumes=True)
        self._deploy_new_app(merged_app)

    def deploy_move_domain(self, merged_app: AppInstance):
        """Deploy same app on another domain."""
        same_label_app = next(
            (app for app in self.apps if app.label_id == merged_app.label_id), None
        )
        important(
            f"Deploy '{merged_app.label}': move {merged_app.app_id} "
            f"from '{same_label_app.domain}' to '{merged_app.domain}'"
        )
        persistent_data = same_label_app.persistent_full_dict()
        self._remove_per_label(same_label_app, remove_volumes=False)
        self._deploy_new_app(merged_app, persistent=persistent_data)

    def deploy_reuse_label(self, merged_app: AppInstance):
        """Deploy another app on another domain."""
        same_label_app = next(
            (app for app in self.apps if app.label_id == merged_app.label_id), None
        )
        important(
            f"Deploy '{merged_app.label}': remove {same_label_app.app_id} "
            f"from '{same_label_app.domain}' and\n"
            f"install {merged_app.app_id} to '{merged_app.domain}'"
        )
        # do not keep data:
        self._remove_per_label(same_label_app, remove_volumes=True)
        self._deploy_new_app(merged_app)

    def _remove_per_label(
        self,
        current_app: AppInstance,
        remove_volumes: bool = False,
    ):
        self.remove_nginx_configuration(current_app.domain)
        self.deployed_domains = [
            d for d in self.deployed_domains if d != current_app.domain
        ]
        self.stop_deployed_apps([current_app])
        self.remove_container_and_network([current_app])
        if remove_volumes:
            self.remove_managed_volumes([current_app])
        with verbosity(3):
            debug("remove_deployed_instance:")
            debug(current_app.label_id)
        self.remove_deployed_instance([current_app])

    def merge_add(self, additional: AppDeployment):
        """Merge by simple addtion of new domain to list."""
        with verbosity(3):
            debug(f"self.deployed_domains       {self.deployed_domains}")
            debug(f"additional.deployed_domains {additional.deployed_domains}")
        conflict = known_strings(self.deployed_domains, additional.deployed_domains)
        if conflict:
            raise Abort(
                f"Some required domains are already deployed: {', '.join(conflict)}\n"
                "Merge with strict add do not allow domain conflicts"
            )
        conflict = known_strings(self.deployed_labels, additional.deployed_labels)
        if conflict:
            raise Abort(
                f"Some required labels are already deployed: {', '.join(conflict)}\n"
                "Merge with strict add do not allow label conflicts (for now)"
            )
        # Note: additional should read from DB the already allocated ports:
        additional.configure_apps()
        self.store_initial_deployment_state()
        self.already_deployed_domains = set(self.deployed_domains)
        self.already_deployed_labels = set(self.deployed_labels)
        self.apps.extend(additional.apps)
        self.sort_apps_per_name_domain()
        self.deployed_domains = sorted(
            {apps_dom["hostname"] for apps_dom in self.apps_per_domain}
        )
        self.deployed_labels = sorted(app.label_id for app in self.apps)
        self.merge_nginx_configuration()
        self._start_apps(additional.apps, deactivate=True)

    def instances_of_domain(self, domain: str) -> list[AppInstance]:
        """Select deployed instances of domain."""
        self.load_deployed_configuration()
        for apps_dom in self.apps_per_domain:
            if apps_dom["hostname"] == domain:
                return apps_dom["apps"]
        raise Abort(f"No instance found for domain '{domain}'")

    def instance_of_label(self, label: str) -> AppInstance:
        """Select deployed instances per label."""
        label_id = AppInstance.docker_sanitized_name(label)
        self.load_deployed_configuration()
        for app in self.apps:
            if app.label_id == label_id:
                return app
        raise Abort(f"No instance found for label_id '{label_id}'")

    def restore_previous_deploy_config_strict(self):
        """Retrieve last successful deployment configuration (strict mode)."""
        with verbosity(0):
            show("Deploy apps from previous deployment (strict mode).")
        self.load_deployed_configuration()

    def restore_previous_deploy_config_replay(self):
        """Retrieve last successful deployment configuration (replay mode)."""
        with verbosity(0):
            show("Deploy apps from previous deployment (replay deployment).")
        self.load_deployed_configuration()
        with verbosity(3):
            self.print_host_list()

    def gather_requirements(self):
        self.install_required_images()
        self.install_required_resources()

    def configure_apps(self):
        self.configure_apps_step1()
        self.configure_apps_step2()
        self.configure_apps_step3()

    def configure_apps_step1(self):
        """ "First part of app configuration: data local to app."""
        self.apps_set_network_name()
        self.apps_set_resources_names()
        self.apps_merge_app_instances_to_resources()
        self.apps_configure_requested_db()
        self.apps_set_volumes_names()
        self.apps_check_local_service_available()
        self.apps_retrieve_persistent()
        self.apps_evaluate_dynamic_values()

    def configure_apps_step2(self):
        """ "Second part of app configuration: common data (ports)."""
        self.apps_generate_ports()

    def configure_apps_step3(self):
        """ "Last part of app configuration: requiring ports."""
        self.apps_parse_healthcheck()
        self.apps_check_host_services_configuration()

    def restore_configure(self):
        """Try to reuse the previous configuration with no change."""
        self.apps_check_local_service_available()
        self.apps_check_host_services_configuration()

    def store_initial_deployment_state(self):
        """Register in store the initial state before changes."""
        self.store_deploy_configs_before_swap()
        self.orig_mounted_volumes = store.list_instances_container_active_volumes()

    def deactivate_previous_apps(self):
        deactivate_all_instances()

    def restore_deactivate_previous_apps(self):
        """For restore situation, find all instance in DB.

        - remove container if exists
        - remove site from Nua DB
        """
        self.orig_mounted_volumes = store.list_instances_container_active_volumes()
        deactivate_all_instances()

    def apply_nginx_configuration(self):
        """Apply configuration to Nginx, especially configurations that can not be
        deployed before all previous apps are stopped."""
        self.configure_nginx()
        # registering https apps with certbot requires that the base nginx config is
        # deployed.
        register_certbot_domains(self.apps)
        with verbosity(3):
            bold_debug("AppDeployment .apps:")
            debug(pformat(self.apps))

    def merge_nginx_configuration(self):
        """Apply configuration to Nginx, when apps are already deployed."""
        if not self.already_deployed_domains:
            # easy, either first deployment or all apps removed, start from zero:
            return self.apply_nginx_configuration()
        for host in self.apps_per_domain:
            hostname = host["hostname"]
            with verbosity(3):
                debug(f"merge_nginx_configuration for {hostname}")
            if hostname in self.already_deployed_domains:
                with verbosity(3):
                    debug("continue, already_deployed_domains")
                continue
            with verbosity(1):
                info(f"Configure Nginx for domain '{hostname}'")
            configure_nginx_hostname(host)
        # registering https apps with certbot requires that the base nginx config is
        # deployed.
        register_certbot_domains(self.apps)
        with verbosity(3):
            bold_debug("AppDeployment .apps:")
            debug(self.apps)

    def remove_nginx_configuration(self, stop_domain: str):
        """Remove apps from the nginx configuration.

        To stop nginx redirection before actually stopping the apps.
        """
        with verbosity(0):
            info(f"Remove Nginx configuration: '{stop_domain}'")

        remove_nginx_configuration_hostname(stop_domain)
        nginx_reload()

    def remove_all_deployed_nginx_configuration(self):
        """Remove all deployed apps from the nginx configuration.

        To stop nginx redirection before actually stopping the apps.
        """
        if not self.deployed_domains:
            return
        with verbosity(0):
            show("Removing Nginx configuration.")
        for domain in self.deployed_domains:
            remove_nginx_configuration_hostname(domain)
        nginx_reload()

    def _start_apps(self, new_apps: list[AppInstance], deactivate: bool = False):
        """Start new deployed apps."""
        if not self.already_deployed_domains:
            # easy, either first deployment or all apps removed, start from zero:
            return self.start_apps()
        # restarting local services:
        self.restart_local_services()
        for app in new_apps:
            if deactivate:
                deactivate_app(app)
            self.start_network(app)
            self.evaluate_container_params(app)
            self.start_resources_containers(app)
            self.setup_resources_db(app)
            self.merge_volume_only_resources(app)
            self.start_main_app_container(app)
            app.running_status = RUNNING
            self.store_container_instance(app)
        chown_r_nua_nginx()
        nginx_reload()

    def start_apps(self):
        """Start all apps to deploy."""
        # restarting local services:
        self.restart_local_services()
        for app in self.apps:
            deactivate_app(app)
            self.start_network(app)
            self.evaluate_container_params(app)
            self.start_resources_containers(app)
            self.setup_resources_db(app)
            self.merge_volume_only_resources(app)
            self.start_main_app_container(app)
            app.running_status = RUNNING
            self.store_container_instance(app)
        chown_r_nua_nginx()
        nginx_restart()

    def start_deployed_apps(self, domain: str, apps: list[AppInstance]):
        """Start deployed instances previously stopped."""
        with verbosity(0):
            info(f"Start instance of domain '{domain}'.")
        for site in apps:
            # self.start_network(site)
            start_one_app_containers(site)
            site.running_status = RUNNING
            self.store_container_instance(site)

    def remove_app_list(self, apps: list[AppInstance]):
        self.stop_deployed_apps(apps)
        self.remove_container_and_network(apps)
        self.remove_managed_volumes(apps)
        self.remove_deployed_instance(apps)

    def stop_deployed_apps(self, apps: list[AppInstance]):
        """Stop deployed app instances."""
        with verbosity(0):
            for app in apps:
                info(f"Stop app '{app.label_id}'")
        for app in apps:
            stop_one_app_containers(app)
            app.running_status = STOPPED
            self.store_container_instance(app)

    def stop_all_deployed_apps(self, store_status: bool = False):
        """Stop all deployed app instances."""
        if not self.apps:
            return
        with verbosity(0):
            show("Stop all instances.")
        for site in self.apps:
            stop_one_app_containers(site)
            if store_status:
                site.running_status = STOPPED
                self.store_container_instance(site)

    def restart_deployed_apps(self, domain: str, apps: list[AppInstance]):
        """Restart deployed instances."""
        with verbosity(0):
            info(f"Restart instance of domain '{domain}'.")
        for site in apps:
            # self.start_network(site)
            restart_one_app_containers(site)
            site.running_status = RUNNING
            self.store_container_instance(site)

    def remove_container_and_network(self, apps: list[AppInstance]):
        """Remove stopped app: container, network, but not volumes."""
        with verbosity(3):
            debug(f"Remove instances '{apps}'")
        self._mounted_before_removing = store.list_instances_container_active_volumes()
        for app in apps:
            deactivate_app(app)
            remove_container_private_network(app.network_name)

    def remove_all_deployed_container_and_network(self):
        """Remove all (stopped) apps container, network, but not volumes."""
        if not self.apps:
            return
        with verbosity(0):
            show("Remove all instances.")
        self._mounted_before_removing = store.list_instances_container_active_volumes()
        for site in self.apps:
            deactivate_app(site)
            remove_container_private_network(site.network_name)

    @staticmethod
    def _local_volumes_dict(volume_list: list) -> dict:
        return {
            item["source"]: item
            for item in volume_list
            if item["type"] == "volume" and item["driver"] == "local"
        }

    def remove_managed_volumes(self, apps: list[AppInstance]):
        """Remove data of stopped app: local managed volumes."""
        before = self._local_volumes_dict(self._mounted_before_removing)
        now_used = self._local_volumes_dict(
            store.list_instances_container_active_volumes()
        )
        for source in before:
            if source not in now_used:
                remove_volume_by_source(source)

    def remove_all_deployed_managed_volumes(self):
        """Remove local volumes of all (stopped) apps."""
        before = self._local_volumes_dict(self._mounted_before_removing)
        for source in before:
            remove_volume_by_source(source)

    def remove_deployed_instance(self, apps: list[AppInstance]):
        """Remove data of stopped app: local managed volumes."""
        with verbosity(3):
            info(f"Remove instance '{apps}' from loaded configuration")
        for app in apps:
            self.remove_app_instance(app)

    def parse_deploy_apps(self):
        """Make the list of AppInstances to be deployed/merged.

        Check config syntax, replace missing information by defaults.
        """
        apps = []
        for site_dict in self.loaded_config["site"]:
            if not isinstance(site_dict, dict):
                raise Abort(
                    "AppInstance configuration must be a dict",
                    explanation=f"{pformat(site_dict)}",
                )

            app_instance = AppInstance(site_dict)
            app_instance.check_valid()
            apps.append(app_instance)
        self.apps = apps

    def sort_apps_per_name_domain(self):
        """Classify the apps per domain, filtering out miss declared apps.

        The apps per domain are available in self.apps_per_domain
        """
        self._filter_duplicate_labels()
        self._make_apps_per_domain()
        self._filter_miss_located_apps()
        self._update_apps_list()

    def _filter_duplicate_labels(self) -> None:
        """Warn about duplicate label and remove the duplicate.

        Note:
            - It's a basic feature for consistency, not a security feature
              about currently deployed instances.
        """
        filtered = []
        known_labels = set()
        for app in self.apps:
            label_id = app.label_id
            if label_id in known_labels:
                warning(f"Duplicate label '{label_id}'. Skipped.")
                continue
            filtered.append(app)
            known_labels.add(label_id)
        self.apps = filtered

    def _make_apps_per_domain(self) -> None:
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

    def _filter_miss_located_apps(self) -> None:
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
            raise Abort("Missing Nua images")

        self.install_images()

    def find_all_apps_images(self) -> bool:
        for app in self.apps:
            if not app.find_registry_path():
                show(f"No image found for '{app.image}'")
                return False
        with verbosity(0):
            seen = set()
            for app in self.apps:
                if app.image not in seen:
                    seen.add(app.image)
                    info(f"Image found: '{app.image}'")
        return True

    def install_images(self):
        start_container_engine()
        installed = {}
        for site in self.apps:
            if not site.find_registry_path(cached=True):
                raise Abort(f"No image found for '{site.image}'")

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
        if not self.pull_all_resources_images():
            raise Abort("Missing Docker images")

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
                debug("pull docker resource:", resource)
            return pull_resource_container(resource)
        return True

    def apps_check_local_service_available(self):
        self.required_services = {s for site in self.apps for s in site.local_services}
        with verbosity(3):
            debug("required services:", self.required_services)
        available_services = set(self.available_services.keys())
        for service in self.required_services:
            if service not in available_services:
                raise Abort(f"Required service '{service}' is not available")

    def apps_check_host_services_configuration(self):
        for site in self.apps:
            for service in site.local_services:
                handler = self.available_services[service]
                if not handler.check_site_configuration(site):
                    raise Abort(
                        f"Required service '{service}' not configured for "
                        f"site {site.domain}"
                    )

    def apps_parse_resources(self):
        for app in self.apps:
            app.parse_resources()

    def apps_parse_healthcheck(self):
        for app in self.apps:
            app.parse_healthcheck()
        with verbosity(3):
            debug("apps_parse_healthcheck() done")

    def apps_set_network_name(self):
        for app in self.apps:
            app.set_network_name()
        with verbosity(3):
            debug("apps_set_network_name() done")

    def apps_set_resources_names(self):
        for app in self.apps:
            app.set_resources_names()
        with verbosity(3):
            debug("apps_set_resources_names() done")

    def apps_merge_app_instances_to_resources(self):
        """Merge configuration declared in the AppInstance config to original
        nua-config declarations."""
        for app in self.apps:
            app.merge_instance_to_resources()
        with verbosity(3):
            debug("apps_merge_instances_to_resources() done")

    def apps_configure_requested_db(self):
        for app in self.apps:
            for resource in app.resources:
                resource.configure_db()
        with verbosity(3):
            debug("apps_configure_requested_db() done")

    def apps_set_volumes_names(self):
        for app in self.apps:
            app.set_volumes_names()
        with verbosity(3):
            debug("apps_set_volumes_names() done")

    def restart_local_services(self):
        with verbosity(1):
            if self.required_services:
                show("Services to restart:", pformat(self.required_services))
            else:
                info("Services to restart: None")
        for service in self.required_services:
            handler = self.available_services[service]
            handler.restart()

    def configure_nginx(self):
        clean_nua_nginx_default_site()
        for host in self.apps_per_domain:
            with verbosity(0):
                info(f"Configure Nginx for domain '{host['hostname']}'")
            configure_nginx_hostname(host)

    def reconfigure_nginx_domain(self, domain: str):
        for host in self.apps_per_domain:
            if host["hostname"] != domain:
                continue
            with verbosity(0):
                info(f"Configure Nginx for domain '{host['hostname']}'")
            configure_nginx_hostname(host)
        nginx_reload()

    def apps_generate_ports(self):
        start_ports = config.read("nua", "ports", "start") or 8100
        end_ports = config.read("nua", "ports", "end") or 9000
        allocated_ports = self.configured_ports()
        with verbosity(4):
            debug(f"apps_generate_ports(): {allocated_ports=}")
        # list of ports used for domains / apps, trying to keep them unchanged
        ports_instances_domains = store.ports_instances_domains()
        with verbosity(4):
            debug(f"apps_generate_ports(): {ports_instances_domains=}")
        allocated_ports.update(ports_instances_domains)
        with verbosity(3):
            debug(f"apps_generate_ports() used ports:\n {allocated_ports=}")
        self.apps_allocate_ports(
            port_allocator(start_ports, end_ports, allocated_ports)
        )
        with verbosity(3):
            debug("apps_generate_ports() done")

    def configured_ports(self) -> set[int]:
        """Return set of required host ports (aka non auto ports) from
        site_list.

        Returns: set of integers
        """
        used = set()
        for app in self.apps:
            used.update(app.used_ports())
        return used

    def apps_allocate_ports(self, allocator: Callable):
        """Update site dict with auto generated ports."""
        for app in self.apps:
            app.allocate_auto_ports(allocator)
            for resource in app.resources:
                resource.allocate_auto_ports(allocator)

    def evaluate_container_params(self, app: AppInstance):
        """Compute site run environment parameters except those requiring late
        evaluation (i.e. host names of started containers)."""
        self.generate_app_container_run_parameters(app)
        for resource in app.resources:
            self.generate_resource_container_run_parameters(resource)

    def apps_retrieve_persistent(self):
        for app in self.apps:
            self.retrieve_persistent(app)

    def retrieve_persistent(self, app: AppInstance):
        previous = store.instance_persistent(app.label_id)
        with verbosity(4):
            debug(f"persistent previous: {previous=}")
        previous.update(app.persistent_full_dict())
        app.set_persistent_full_dict(previous)

    def apps_evaluate_dynamic_values(self):
        for app in self.apps:
            self.evaluate_dynamic_values(app)

    def evaluate_dynamic_values(self, app: AppInstance):
        ordered_resources = app.order_resources_dependencies()
        for resource in ordered_resources:
            if resource == app:
                self.generate_app_env_port_values(app)
            else:
                self.generate_resource_env_port_values(app, resource=resource)

    def generate_app_env_port_values(self, app: AppInstance):
        run_env = deepcopy(app.env)
        run_env.update(instance_key_evaluator(app, late_evaluation=False))
        app.env = run_env
        new_port_list = []
        for port in app.port_list:
            new_port = deepcopy(port)
            new_port.update(
                instance_key_evaluator(
                    app,
                    port=port,
                    late_evaluation=False,
                )
            )
            new_port_list.append(new_port)
        app.port_list = new_port_list

    def generate_resource_env_port_values(self, app: AppInstance, resource: Resource):
        run_env = deepcopy(resource.env)
        run_env.update(
            instance_key_evaluator(app, resource=resource, late_evaluation=False)
        )
        resource.env = run_env

    def start_network(self, app: AppInstance):
        if app.network_name:
            create_container_private_network(app.network_name)

    def start_resources_containers(self, app: AppInstance):
        for resource in app.resources:
            if resource.is_docker_type():
                mounted_volumes = mount_resource_volumes(resource)
                start_one_container(resource, mounted_volumes)
                # until we check startup of container or set value in parameters...
                time.sleep(2)

    def setup_resources_db(self, app: AppInstance):
        for resource in app.resources:
            resource.setup_db()

    def merge_volume_only_resources(self, app: AppInstance):
        for resource in app.resources:
            if resource.volume_declaration:
                app.volume = app.volume + resource.volume_declaration

    def start_main_app_container(self, app: AppInstance):
        # volumes need to be mounted before beeing passed as arguments to
        # docker.run()
        mounted_volumes = mount_resource_volumes(app)
        start_one_container(app, mounted_volumes)

    def store_container_instance(self, app: AppInstance):
        with verbosity(3):
            bold_debug("Saving AppInstance configuration in Nua DB")
        store.store_instance(
            app_id=app.app_id,
            label_id=app.label_id,
            nua_tag=app.nua_tag,
            domain=app.domain,
            container=app.container_name,
            image=app.image,
            state=app.running_status,
            site_config=dict(app),
        )

    def generate_app_container_run_parameters(self, app: AppInstance):
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
        nua_conf_docker = deepcopy(app.image_nua_config.get("docker", {}))
        if "env" in nua_conf_docker:
            del nua_conf_docker["env"]
        run_params.update(nua_conf_docker)
        # update with parameters that could be added to AppInstance configuration :
        run_params.update(app.get("docker", {}))
        # Add the hostname/IP of local Docker hub (Docker feature) :
        self.add_host_gateway_to_extra_hosts(run_params)
        run_params["name"] = app.container_name
        run_params["ports"] = app.ports_as_docker_params()
        run_params["environment"] = app.env
        if app.healthcheck:
            run_params["healthcheck"] = HealthCheck(app.healthcheck).as_docker_params()
        self.sanitize_run_params(run_params)
        app.run_params = run_params

    def generate_resource_container_run_parameters(
        self,
        resource: Resource,
    ):
        """Return suitable parameters for the docker.run() command (for
        Resource)."""
        run_params = deepcopy(RUN_BASE_RESOURCE)
        run_params.update(resource.docker)
        self.add_host_gateway_to_extra_hosts(run_params)
        run_params["name"] = resource.container_name
        run_params["ports"] = resource.ports_as_docker_params()
        run_params["environment"] = resource.env
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

    @staticmethod
    def sanitize_run_params(run_params: dict):
        """Docker constraint: 2 docker options not compatible."""
        if "restart_policy" in run_params:
            run_params["auto_remove"] = False

    def services_environment(self, app: AppInstance) -> dict:
        run_env = {}
        for service in app.local_services:
            handler = self.available_services[service]
            # function may need or not site param:
            run_env.update(handler.environment(app))
        return run_env

    def resources_environment(self, app: AppInstance) -> dict:
        run_env = {}
        for resource in app.resources:
            run_env.update(resource.environment_ports())
        return run_env

    def post_deployment(self):
        self.store_deploy_configs_after_swap()
        self.display_deployment_status()

    def post_full_uninstall(self, display: bool = False):
        self.loaded_config = {}
        self.apps = []
        self.store_deploy_configs_after_swap()
        if display:
            self.display_deployment_status()

    def display_deployment_status(self):
        self.display_deployed_apps()
        self.display_used_volumes()
        self.display_unused_volumes()

    def display_deployed_apps(self):
        if not self.apps:
            important("No app deployed.")
            return

        important("Deployed apps:")
        protocol = protocol_prefix()
        for app in self.apps:
            msg = f"Label: {app.label_id}"
            info(msg)
            msg = f"Image '{app.image}' deployed as {protocol}{app.domain}"
            info(msg)
            msg = f"Deployment status: {app.running_status}"
            info(msg)
            self.display_persistent_data(app)
        vprint("")

    def display_persistent_data(self, app: AppInstance):
        with verbosity(3):
            content = app.persistent_full_dict()
            if content:
                bold_debug("Persistent generated variables:")
                debug(pformat(content))

    def display_used_volumes(self):
        with verbosity(0):
            current_mounted = store.list_instances_container_active_volumes()
            if not current_mounted:
                return
            important("Volumes used by current Nua configuration:")
            for volume in current_mounted:
                show(Volume.string(volume))

    def display_unused_volumes(self):
        with verbosity(0):
            unused = unused_volumes(self.orig_mounted_volumes)
            if not unused:
                return
            important(
                "Some volumes are mounted but not used by current Nua configuration:"
            )
            for volume in unused:
                show(Volume.string(volume))

    def print_host_list(self):
        # used with verbosity 3
        bold_debug("apps per domain:\n")
        debug(pformat(self.apps_per_domain))


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
            red_line(f"    {image=} / {site['domain']}")

    host["apps"] = valid_apps
    host["located"] = False
