"""Functions to respond to requirement from instance declarations."""

from copy import deepcopy
from functools import wraps
from typing import Any

from nua.lib.panic import error, warning
from nua.runtime.gen_password import gen_password

from .resource import Resource
from .site import Site

# keys of nua-config file:
KEY = "key"
SITE_ENVIRONMENT = "environment"
PERSISTENT = "persistent"
RESOURCE_PROPERTY = "resource_property"
RESOURCE_HOST = "resource_host"
NUA_INTERNAL = "nua_internal"


def persistent_value(func):
    """Store automatic generated values for next deployment of the same image.

    Default is 'persistent = true'.
    If persistent is False, erase the data from *local* config storage.
    """

    @wraps(func)
    def wrapper(site: Site, requirement: dict) -> Any:
        if requirement.get(PERSISTENT, True):
            value = site.persistent.get(requirement[KEY])
            if value is None:
                result = func(site, requirement)
                site.persistent[requirement[KEY]] = result[requirement[KEY]]
            else:
                result = {requirement[KEY]: value}
            return result
        # persistent is False: erase past value if needed
        if requirement[KEY] in site.persistent:
            persist = deepcopy(site.persistent)
            del persist[requirement[KEY]]
            site.persistent = persist
        return func(site, requirement)

    return wrapper


@persistent_value
def random_str(site: Site, requirement: dict) -> dict:
    """Send a password.

    - ramdom generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return {requirement[KEY]: gen_password(24)}


def resource_property(site: Site, requirement: dict) -> dict:
    values = requirement[RESOURCE_PROPERTY].split(".")
    if len(values) != 2:
        error(f"Bad content for resource_property: {requirement}")
    resource_name, prop = values
    for resource in site.resources:
        if resource.resource_name != resource_name:
            continue
        # first try in environ variables of differnt kinds
        if prop in resource.run_env:
            value = resource.run_env[prop]
        elif hasattr(resource, prop):
            attr = getattr(resource, prop)
            if callable(attr):
                value = str(attr())
            else:
                value = str(attr)
        else:
            error(f"Unknown property for resource_property: {requirement}")
        return {requirement[KEY]: value}
    warning(f"Unknown resource for {requirement}")
    return {}


def resource_host(site: Site, requirement: dict) -> dict:
    """Return a dict whose key is a environment variable name and value the the
    hostname of a resource (a container).
    """
    resource_name = requirement[RESOURCE_HOST] or ""
    for resource in site.resources:
        if resource.resource_name != resource_name:
            continue
        return {requirement[KEY]: resource.container}
    warning(f"Unknown resource for resource_host: {requirement}")
    return {}


def site_environment(rsite: Resource, requirement: dict) -> dict:
    variable = requirement[SITE_ENVIRONMENT] or ""
    # The resource environment was juste completed wth Site's environment:
    env = rsite.run_env
    if variable in env:
        return {requirement[KEY]: env.get(variable)}
    warning(f"Unknown variable in environment: {variable}")
    return {}


def nua_internal(site: Site, requirement: dict) -> dict:
    """Retrieve key from nua_internal values, do not store the value in
    instance configuration.

    The value is only set when executing the docker.run() for main site
    and all sub resources.
    """
    if requirement.get(NUA_INTERNAL, False):
        # add the key to the list of secrets to pass at run() time
        site.add_requested_secrets(requirement[KEY])
    return {}
