"""Functions to respond to requirement from instance declarations.

All evaluation function must have same 2 arguments:
    function(resource, requirement)
but call through wrapper uses a third argument: 'persistent'

"""
from functools import wraps
from typing import Any

from nua.lib.panic import abort, warning
from nua.runtime.gen_password import gen_password

from ..persistent import Persistent
from ..resource import Resource
from .db_utils import generate_new_db_id, generate_new_user_id

# keys of nua-config file:
KEY = "key"
SITE_ENVIRONMENT = "environment"
PERSISTENT = "persistent"
RESOURCE_PROPERTY = "resource_property"
NUA_INTERNAL = "nua_internal"


def persistent_value(func):
    """Store automatic generated values for next deployment of the same image.

    Default is 'persistent = true'.
    If persistent is False, erase the data from *local* config storage.
    """

    @wraps(func)
    def wrapper(resource: Resource, requirement: dict, persistent: Persistent) -> Any:
        if requirement.get(PERSISTENT, True):
            value = persistent.get(requirement[KEY])
            if value is None:
                result = func(resource, requirement)
                persistent[requirement[KEY]] = result[requirement[KEY]]
            else:
                result = {requirement[KEY]: value}
            return result
        # persistent is False: erase past value if needed then return computed value
        persistent.delete(requirement[KEY])
        return func(resource, requirement)

    return wrapper


def no_persistent_value(func):
    """Dummy wrapper to remove thirf argument."""

    @wraps(func)
    def wrapper(resource: Resource, requirement: dict, _persistent: Persistent) -> Any:
        return func(resource, requirement)

    return wrapper


@persistent_value
def random_str(resource: Resource, requirement: dict) -> dict:
    """Send a password.

    - ramdom generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return {requirement[KEY]: gen_password(24)}


@persistent_value
def unique_user(resource: Resource, requirement: dict) -> dict:
    """Send a unique user id (for DB creation).

    - sequential generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return {requirement[KEY]: generate_new_user_id()}


@persistent_value
def unique_db(resource: Resource, requirement: dict) -> dict:
    """Send a unique DB id (for DB creation).

    - sequential generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return {requirement[KEY]: generate_new_db_id()}


@no_persistent_value
def resource_property(rsite: Resource, requirement: dict) -> dict:
    values = requirement[RESOURCE_PROPERTY].split(".")
    if len(values) != 2:
        abort(f"Bad content for resource_property: {requirement}")
    resource_name, prop = values
    for resource in rsite.resources:
        if resource.resource_name != resource_name:
            continue
        # first try in environ variables of differnt kinds
        print(prop)
        print(resource.run_env)
        if prop in resource.run_env:
            value = resource.run_env[prop]
        elif hasattr(resource, prop):
            attr = getattr(resource, prop)
            if callable(attr):
                value = str(attr())
            else:
                value = str(attr)
        else:
            abort(f"Unknown property for resource_property: {requirement}")
        return {requirement[KEY]: value}

    warning(f"Unknown resource for {requirement}")
    return {}


@no_persistent_value
def site_environment(rsite: Resource, requirement: dict) -> dict:
    variable = requirement[SITE_ENVIRONMENT] or ""
    # The resource environment was juste completed wth Site's environment:
    env = rsite.run_env
    if variable in env:
        return {requirement[KEY]: env.get(variable)}
    warning(f"Unknown variable in environment: {variable}")
    return {}


@no_persistent_value
def nua_internal(rsite: Resource, requirement: dict) -> dict:
    """Retrieve key from nua_internal values, do not store the value in
    instance configuration.

    The value is only set when executing the docker.run() for main site
    and all sub resources.
    """
    if requirement.get(NUA_INTERNAL, False):
        # add the key to the list of secrets to pass at run() time
        rsite.add_requested_secrets(requirement[KEY])
    return {}
