"""Functions to respond to requirement from instance declarations.

All evaluation function must have same 2 arguments:
function(provider, requirement) but call through wrapper uses a third
argument: 'persistent'
"""
from functools import wraps
from typing import Any

from nua.lib.gen_password import gen_password, gen_randint
from nua.lib.panic import Abort, show, warning
from nua.lib.tool.state import verbosity

from ..net_utils.external_ip import external_ip
from ..persistent import Persistent
from ..provider import Provider
from ..volume import Volume
from .gen_db_credentials import generate_new_db_id, generate_new_user_id

SITE_ENVIRONMENT = "environment"
PERSISTENT = "persistent"
NUA_INTERNAL = "nua_internal"


def persistent_value(func):
    """Store automatic generated values for next deployment of the same image.

    Default is 'persistent = true'.
    If persistent is False, erase the data from *local* config storage.
    """

    @wraps(func)
    def wrapper(
        provider: Provider,
        destination_key: str,
        requirement: dict,
        persistent: Persistent,
    ) -> Any:
        if requirement.get(PERSISTENT, True):
            value = persistent.get(destination_key)
            if value is None:
                result = func(provider, destination_key, requirement)
                persistent[destination_key] = result[destination_key]
            else:
                result = {destination_key: value}
            return result
        # persistent is False: erase past value if needed then return computed value
        persistent.delete(destination_key)
        return func(provider, destination_key, requirement)

    return wrapper


def no_persistent_value(func):
    """Wrapper to mask of the persistent argument."""

    @wraps(func)
    def wrapper(
        provider: Provider,
        destination_key: str,
        requirement: dict,
        _persistent: Persistent,
    ) -> Any:
        return func(provider, destination_key, requirement)

    return wrapper


@persistent_value
def random(provider: Provider, destination_key: str, requirement: dict) -> dict:
    """Send a random string or a random integer.

    The value is either ramdomly generated or read from previous
    execution if 'persistent' is true (default) and previous data is
    found. Default length for random string is 24. Random integer is a
    64 bit positive signed, [0, 2*64-1]
    """
    tpe = requirement.get("type", "string")
    if tpe.lower() in {"int", "integer"}:
        return {destination_key: gen_randint()}
    length = max(1, int(requirement.get("length", 24)))
    if length < 8:
        warning(f"A random string of length {length} would result in a weak password")
    return {destination_key: gen_password(length)}


@persistent_value
def unique_user(
    provider: Provider,
    destination_key: str,
    requirement: dict,
) -> dict:
    """Send a unique user id (for DB creation).

    - sequential generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return {destination_key: generate_new_user_id()}


@persistent_value
def unique_db(provider: Provider, destination_key: str, requirement: dict) -> dict:
    """Send a unique DB id (for DB creation).

    - sequential generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return {destination_key: generate_new_db_id()}


def _query_provider(source_name: str, rsite: Provider) -> Provider | None:
    if not source_name:
        return rsite
    for provider in rsite.providers:
        if provider.provider_name == source_name:
            return provider
    return None


def _query_volume(source_name: str, rsite: Provider) -> Volume | None:
    if not source_name:
        return None
    for volume_dict in rsite.volumes:
        if volume_dict.get("name", "") == source_name:
            return Volume.parse(volume_dict)
    return None


@no_persistent_value
def provider_property(
    rsite: Provider,
    destination_key: str,
    requirement: dict,
) -> dict:
    """Retrieve value from provider by name.

    Example:
        CMD_DB_HOST = { from="", key="hostname" }
        CMD_DB_HOST = { from="database", key="hostname" }
        CMD_DB_DATABASE = { from="database", key="POSTGRES_DB" }
    """
    source_name = requirement.get("from", "").strip()
    # if not source_name, consider querying current provider
    property = requirement.get("key", "").strip()
    if not property:
        raise Abort(f"Bad requirement, missing 'key' key : {requirement}")

    # first evaluate against the ressource own volumes:
    volume = _query_volume(source_name, rsite)
    if volume is not None:
        return actual_volume_property(
            volume,
            property,
            destination_key,
            requirement,
        )
    provider = _query_provider(source_name, rsite)
    if provider is not None:
        return actual_provider_property(
            provider, property, destination_key, requirement
        )
    warning(f"Unknown provider name for {requirement}")
    return {}


def actual_provider_property(
    provider: Provider,
    property: str,
    destination_key: str,
    requirement: dict,
) -> dict:
    # first try in environ variables of differnt kinds
    if property in provider.env:
        value = provider.env[property]
    elif hasattr(provider, property):
        attr = getattr(provider, property)
        if callable(attr):
            value = str(attr())
        else:
            value = str(attr)
    else:
        warning("Provider environment:")
        warning(str(provider.env))
        raise Abort(f"Unknown property for: {requirement}")

    with verbosity(4):
        show(f"provider_property {property} ->")
        show(f"    result {destination_key}:{value}")
    return {destination_key: value}


def actual_volume_property(
    volume: Volume,
    property: str,
    destination_key: str,
    requirement: dict,
) -> dict:
    # first try in environ variables of differnt kinds
    if hasattr(volume, property):
        attr = getattr(volume, property)
        if callable(attr):
            value = str(attr())
        else:
            value = str(attr)
    else:
        warning("Volume:")
        warning(str(volume))
        raise Abort(f"Unknown property for: {requirement}")

    with verbosity(4):
        show(f"volume_property {property} ->")
        show(f"    result {destination_key}:{value}")
    return {destination_key: value}


@no_persistent_value
def site_environment(
    rsite: Provider,
    destination_key: str,
    requirement: dict,
) -> dict:
    variable = requirement[SITE_ENVIRONMENT] or ""
    # The provider environment was juste completed wth AppInstance's environment:
    env = rsite.env
    if variable in env:
        return {destination_key: env.get(variable)}
    warning(f"Unknown variable in environment: {variable}")
    return {}


@no_persistent_value
def nua_internal(rsite: Provider, destination_key: str, requirement: dict) -> dict:
    """Retrieve key from nua_internal values, do not store the value in
    instance configuration.

    The value is only set when executing the docker.run() for main site
    and all sub providers.
    """
    if requirement.get(NUA_INTERNAL, False):
        # add the key to the list of secrets to pass at run() time
        rsite.add_requested_secrets(destination_key)
    return {}


@no_persistent_value
def external_ip_evaluation(
    _unused: Provider, destination_key: str, requirement: dict
) -> dict:
    """Return the detected external IP address (v4).

    The value is only set when executing the docker.run() for main site
    and all sub providers.
    """
    return {destination_key: external_ip()}
