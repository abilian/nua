"""Functions to respond to requirement from instance declarations.

All evaluation function must have same 2 arguments:
    function(resource, requirement)
but call through wrapper uses a third argument: 'persistent'

"""
from functools import wraps
from typing import Any

from nua.agent.gen_password import gen_password
from nua.lib.panic import abort, show, warning
from nua.lib.tool.state import verbosity

from ..persistent import Persistent
from ..resource import Resource
from .db_utils import generate_new_db_id, generate_new_user_id

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
        resource: Resource,
        destination_key: str,
        requirement: dict,
        persistent: Persistent,
    ) -> Any:
        if requirement.get(PERSISTENT, True):
            value = persistent.get(destination_key)
            if value is None:
                result = func(resource, destination_key, requirement)
                persistent[destination_key] = result[destination_key]
            else:
                result = {destination_key: value}
            return result
        # persistent is False: erase past value if needed then return computed value
        persistent.delete(destination_key)
        return func(resource, destination_key, requirement)

    return wrapper


def no_persistent_value(func):
    """Dummy wrapper to remove thirf argument."""

    @wraps(func)
    def wrapper(
        resource: Resource,
        destination_key: str,
        requirement: dict,
        _persistent: Persistent,
    ) -> Any:
        return func(resource, destination_key, requirement)

    return wrapper


@persistent_value
def random_str(
    resource: Resource,
    destination_key: str,
    requirement: dict,
) -> dict:
    """Send a password.

    - ramdom generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return {destination_key: gen_password(24)}


@persistent_value
def unique_user(
    resource: Resource,
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
def unique_db(
    resource: Resource,
    destination_key: str,
    requirement: dict,
) -> dict:
    """Send a unique DB id (for DB creation).

    - sequential generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return {destination_key: generate_new_db_id()}


def _query_resource(source_name: str, rsite: Resource) -> Resource | None:
    if not source_name:
        return rsite
    for resource in rsite.resources:
        if resource.resource_name == source_name:
            return resource
    return None


@no_persistent_value
def resource_property(
    rsite: Resource,
    destination_key: str,
    requirement: dict,
) -> dict:
    """Retrieve value from resource by name.

    Example:
        CMD_DB_HOST = { from="", key="hostname" }
        CMD_DB_HOST = { from="database", key="hostname" }
        CMD_DB_DATABASE = { from="database", key="POSTGRES_DB" }
    """
    source_name = requirement.get("from", "").strip()
    # if not source_name, consider querying current resource
    property = requirement.get("key", "").strip()
    if not property:
        abort(f"Bad requirement, missing 'key' key : {requirement}")
    resource = _query_resource(source_name, rsite)
    if not resource:
        warning(f"Unknown resource name for {requirement}")
        return {}
    # first try in environ variables of differnt kinds
    if property in resource.env:
        value = resource.env[property]
    elif hasattr(resource, property):
        attr = getattr(resource, property)
        if callable(attr):
            value = str(attr())
        else:
            value = str(attr)
    else:
        abort(f"Unknown property for: {requirement}")
    with verbosity(4):
        show(f"resource_property {source_name}:{property} ->")
        show(f"    result {destination_key}:{value}")
    return {destination_key: value}


@no_persistent_value
def site_environment(
    rsite: Resource,
    destination_key: str,
    requirement: dict,
) -> dict:
    variable = requirement[SITE_ENVIRONMENT] or ""
    # The resource environment was juste completed wth AppInstance's environment:
    env = rsite.env
    if variable in env:
        return {destination_key: env.get(variable)}
    warning(f"Unknown variable in environment: {variable}")
    return {}


@no_persistent_value
def nua_internal(
    rsite: Resource,
    destination_key: str,
    requirement: dict,
) -> dict:
    """Retrieve key from nua_internal values, do not store the value in
    instance configuration.

    The value is only set when executing the docker.run() for main site
    and all sub resources.
    """
    if requirement.get(NUA_INTERNAL, False):
        # add the key to the list of secrets to pass at run() time
        rsite.add_requested_secrets(destination_key)
    return {}
