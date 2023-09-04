from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from operator import attrgetter
from pathlib import Path
from pprint import pformat
from typing import Any

from nua.lib.docker import docker_sanitized_name
from nua.lib.normalization import normalize_ports, ports_as_list
from nua.lib.nua_config import hyphen_get
from nua.lib.nua_tag import nua_tag_string
from nua.lib.panic import Abort, debug, info, warning
from nua.lib.tool.state import verbosity

from .backup.backup_record import BackupRecord
from .db.model.instance import STOPPED
from .domain_split import DomainSplit
from .persistent import Persistent
from .port_utils import rebase_ports_on_defaults
from .provider import Provider
from .provider_deps import ProviderDeps
from .search_cmd import search_nua
from .volume import Volume


class AppInstance(Provider):
    MANDATORY_KEYS = ("image", "domain")

    def __init__(self, app_instance_dict: dict):
        super().__init__(app_instance_dict)
        self.type = "nua-site"

    @classmethod
    def from_dict(cls, app_instance_dict: dict) -> AppInstance:
        app_instance = cls({})
        providers = []
        for provider in app_instance_dict.get("providers", []):
            providers.append(Provider.from_dict(provider))
        for key, val in app_instance_dict.items():
            if key == "providers":
                continue
            app_instance[key] = val
        app_instance["providers"] = providers
        app_instance["port"] = app_instance.get("port") or {}
        return app_instance

    def check_valid(self):
        self._check_mandatory()
        self._normalize_env_values()
        self._normalize_ports()
        self._normalize_domain()
        self._set_label_id()

    @property
    def providers(self) -> list:
        """List of sub providers of the AppInstance object.

        Warning: only AppInstance class has an actual use of 'providers'.
        The subclass Provider will always provide an *empty* list
        """
        return self.get("providers", [])

    @providers.setter
    def providers(self, providers: list):
        self["providers"] = providers

    @property
    def image_nua_config(self) -> dict:
        return self["image_nua_config"]

    @image_nua_config.setter
    def image_nua_config(self, image_nua_config: dict):
        self["image_nua_config"] = image_nua_config

    @property
    def label(self) -> str:
        return self["label"]

    @property
    def top_domain(self) -> str:
        return self["top_domain"]

    @top_domain.setter
    def top_domain(self, top_domain: str):
        self["top_domain"] = top_domain

    @property
    def local_services(self) -> list:
        return [
            provider.service for provider in self.providers if provider.type == "local"
        ]

    @property
    def app_id(self) -> str:
        return self.image_nua_config["metadata"]["id"]

    @property
    def image_short(self) -> str:
        """Return short app id from deployment 'image' value.

        Used early: at that moment the Docker image and actual
        image/nua_config are not available.

        Remove 'nua-' prefix and version):  "nua-hedgedoc" ->
        "hedgedoc".
        """
        image = self.image.strip()
        if image.startswith("nua-"):
            image = image[4:]
        return image.split(":")[0]

    @property
    def nua_tag(self) -> str:
        """Return long tag string with version and release.

        "hedgedoc" -> "nua-hedgedoc:1.9.7-3"
        """
        return nua_tag_string(self.image_nua_config["metadata"])

    @property
    def nua_dash_name(self) -> str:
        return self.nua_tag.replace(":", "-")

    @property
    def container_name(self) -> str:
        # override the method of Provider
        # suffix = DomainSplit(self.domain).container_suffix()
        # name = sanitized_name(f"{self.nua_dash_name}-{suffix}")
        # self["container_name"] = name
        # return name
        return f"{self.label_id}-{self.app_id}"

    @property
    def running_status(self) -> str:
        return self.get("running_status", STOPPED)

    @property
    def backup_records(self) -> list[dict]:
        if "backup_records" not in self:
            self["backup_records"] = []
        return self["backup_records"]

    @backup_records.setter
    def backup_records(self, backup_records: list[dict]):
        self["backup_records"] = backup_records

    @property
    def backup_records_objects(self) -> list[BackupRecord]:
        records = [BackupRecord.from_dict(data) for data in self.backup_records]
        records.sort(key=attrgetter("date_time"))
        return records

    def backup_records_crop(self, max_length: int = 7, max_age: int = 31) -> None:
        """Kepp in the backup_records list the last max_length elements and remove
        the elements olders than max_age

        Note: clean also the local backup directory?"""
        limit_date = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(
            days=max_age
        )
        records = self.backup_records_objects[-max_length:]
        records = [record for record in records if record.date_time >= limit_date]
        self.backup_records = [record.as_dict() for record in records]

    @running_status.setter
    def running_status(self, status: str):
        self["running_status"] = status

    def persistent(self, name: str) -> Persistent:
        """Return Persistent instance for provider of name 'name'.

        Use name = '' for main site.
        """
        if "persistent" not in self:
            self["persistent"] = {}
        content = self["persistent"].get(name, {})
        return Persistent.from_name_dict(name, content)

    def set_persistent(self, persistent: Persistent):
        if "persistent" not in self:
            self["persistent"] = {}
        self["persistent"].update(persistent.as_dict())

    def persistent_full_dict(self) -> dict:
        if "persistent" not in self:
            self["persistent"] = {}
        return self["persistent"]

    def set_persistent_full_dict(self, persist_dict: dict):
        self["persistent"] = persist_dict

    def parse_healthcheck(self):
        self._parse_healthcheck(self.image_nua_config.get("healthcheck") or {})

    def parse_backup(self):
        self._parse_backup(self.image_nua_config.get("backup") or {})

    def set_volumes_names(self):
        # suffix = DomainSplit(self.domain).container_suffix()
        # self.volume = [Volume.update_name_dict(v, suffix) for v in self.volume]
        # for provider in self.providers:
        #     provider.volume = [
        #         Volume.update_name_dict(v, suffix) for v in provider.volume
        #     ]
        self.volumes = [Volume.update_name_dict(v, self.label_id) for v in self.volumes]
        for provider in self.providers:
            provider.volumes = [
                Volume.update_name_dict(v, self.label_id) for v in provider.volumes
            ]

    @property
    def registry_path(self) -> str:
        return self.get("registry_path") or ""

    @registry_path.setter
    def registry_path(self, registry_path: str | Path):
        self["registry_path"] = str(registry_path)

    def set_network_name(self):
        """Evaluate the need of a bridge private network.

        If needed, set a relevant network name.
        """
        self.network_name = ""
        if any(provider.requires_network() for provider in self.providers):
            self.network_name = self.container_name
            for provider in self.providers:
                provider.network_name = self.network_name
            with verbosity(4):
                debug("detect_required_network() network_name =", self.network_name)

    def provider_per_name(self, name: str) -> Provider | None:
        for provider in self.providers:
            if provider.provider_name == name:
                return provider
        return None

    def merged_volumes(self) -> list[dict[str, Any]]:
        volumes = []
        for provider in self.providers:
            if provider.is_docker_type():
                continue
            # need to find a better way
            if provider.volumes:
                volumes.extend(provider.volumes)
        return self.volumes + volumes

    def merge_instance_to_providers(self):
        self.rebase_env_upon_nua_conf()
        self.rebase_volumes_upon_nua_conf()
        self.rebase_ports_upon_nua_config()
        instance_config_providers = self.get("provider") or []
        for update_provider in instance_config_providers:
            self._merge_provider_updates_to_provider(update_provider)
        self["provider"] = None

    def rebase_env_upon_nua_conf(self):
        """Merge AppInstance declared env at deploy time upon base declaration
        of nua-config."""
        base_env = deepcopy(self.image_nua_config.get("env") or {})
        base_env.update(self.env)
        self.env = base_env

    def order_providers_dependencies(self) -> list[Provider]:
        """Order of evaluations for variables.

        - main AppInstance variable assignment (including hostname of providers)
        - late evaluation (hostnames)
        And check for circular dependencies of providers.
        """
        provider_deps = ProviderDeps()
        for provider in self.providers:
            provider_deps.add_provider(provider)
        provider_deps.add_provider(self)
        return provider_deps.solve()

    def _merge_provider_updates_to_provider(self, update_provider: dict[str, Any]):
        if not update_provider:
            # no redefinition of any configuration of the provider
            return
        if not isinstance(update_provider, dict):
            warning(
                f"ignoring update for '{self.domain}' providers, need a dict",
                explanation=pformat(update_provider),
            )
            return
        provider_name = update_provider.get("name")
        if not provider_name or not isinstance(provider_name, str):
            warning(
                "ignoring provider update without name",
                pformat(update_provider),
            )
            return
        provider = self.provider_per_name(provider_name)
        if not provider:
            warning(f"ignoring provider update, unknown provider '{provider_name}'")
            return
        provider.update_from_site_declaration(update_provider)

    def parse_providers(self):
        """Build the providers list or Provider from nua_config.

        The providers will be later updated from site config providers statements.
        Note: there is still a "provider" key for instance changes.
        """
        providers_list = self.image_nua_config.get("provider") or []
        providers = [self._parse_provider(config) for config in providers_list]
        providers = [provider for provider in providers if provider]
        with verbosity(3):
            debug(f"Image providers: {pformat(providers)}")
        self.providers = providers

    def _parse_provider(self, provider_config: dict) -> Provider | None:
        for required_key in ("name", "type"):
            value = provider_config.get(required_key)
            if not value or not isinstance(value, str):
                warning(
                    f"ignoring provider declaration without '{required_key}'",
                    pformat(provider_config),
                )
                return None
        provider = Provider(provider_config)
        # debug backup print(declaration)
        provider.provider_name = provider_config["name"]
        provider.check_valid()
        # print("=" * 40)
        # print(pformat(dict(provider)))
        return provider

    def _normalize_domain(self):
        dom = DomainSplit(self.domain)
        self.domain = dom.full_path()
        self.top_domain = dom.top_domain()

    def _set_label_id(self):
        label = hyphen_get(self, "label") or ""
        if not "_".join(label.split()):
            label = self.default_label()
            with verbosity(0):
                info(f"Label not provided, using default: '{label}'")
        self.set_instance_label(label)

    def default_label(self):
        """Return a label based on app id and domain.

        To use when the user does not provide an app label or as default
        value.
        """
        return f"{self.image_short}-{self.domain}"

    def set_instance_label(self, label: str):
        label_id = docker_sanitized_name(label)
        if not label_id:
            raise ValueError("Empty label is not allowed")
        self.label_id = label_id
        self["label"] = label.strip()

    def rebase_volumes_upon_nua_conf(self):
        self.volumes = self.rebased_volumes_upon_package_conf(self.image_nua_config)

    def rebase_ports_upon_nua_config(self):
        nua_config_ports = deepcopy(self.image_nua_config.get("port") or {})
        if not isinstance(nua_config_ports, dict):
            raise Abort("nua_config['port'] must be a dict")

        base_ports = normalize_ports(ports_as_list(nua_config_ports))
        self.port_list = rebase_ports_on_defaults(base_ports, self.port_list)
        with verbosity(4):
            debug(f"rebase_ports_upon_nua_config(): ports={pformat(self.port_list)}")

    def find_registry_path(self, cached: bool = False) -> bool:
        # list of images sorted by version:
        if cached and self.registry_path:
            return True
        results = self._search_nua_registry()
        if results:
            # results are sorted by version, take higher:
            self.registry_path = results[-1]
        else:
            self.registry_path = ""
        return bool(self.registry_path)

    def _search_nua_registry(self) -> list:
        if self.type not in {"nua-site", "docker"}:
            raise ValueError(f"Unsupported type of container '{self.type}'")
        return search_nua(self.image)

    def set_providers_names(self):
        """Set first container names of providers to permit early host
        assignment to variables.
        """
        for provider in self.providers:
            provider.label_id = self.label_id
            provider.set_container_name()
