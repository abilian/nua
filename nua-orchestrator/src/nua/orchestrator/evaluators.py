"""Functions to respond to requirement from instance declarations."""

from functools import wraps
from typing import Any

from nua.lib.panic import error, warning
from nua.runtime.gen_password import gen_password

from .site import Site

# keys of nua-config file:
KEY = "key"
PERSISTENT = "persistent"
RESOURCE_PROPERTY = "resource_property"


def persistent_value(func):
    @wraps(func)
    def wrapper(site: Site, requirement: dict) -> Any:
        if requirement.get(PERSISTENT, False):
            value = site.persistent.get(requirement[KEY])
            if value is None:
                value = func(site, requirement)
                site.persistent[requirement[KEY]] = value
            return value
        else:
            return func(site, requirement)

    return wrapper


@persistent_value
def random_str(site: Site, requirement: dict) -> str:
    """Send a password
    - ramdom generated,
    - or from previous execution if 'persistent' is true and previous
    data is found.
    """
    return gen_password(24)


def resource_property(site: Site, requirement: dict) -> str:
    values = requirement[RESOURCE_PROPERTY].split(".")
    if len(values) != 2:
        error(f"Bad content for resource_property: {requirement}")
    resource_name, property = values
    for resource in site.resources:
        if resource.resource_name != resource_name:
            continue
        if hasattr(resource, property):
            attr = getattr(resource, property)
            if callable(attr):
                return str(attr())
            else:
                return attr
        else:
            error(f"Bad property for resource_property: {requirement}")
    warning(f"resource not found for {requirement}")
    return ""
