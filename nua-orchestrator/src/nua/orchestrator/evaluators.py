"""Functions to respond to requirement from instance declarations."""

from nua.lib.panic import error, warning
from nua.runtime.gen_password import gen_password

from .site import Site


def random_str(_unused: Site, _unused2: dict) -> str:
    return gen_password(24)


def resource_property(site: Site, requirement: dict) -> str:
    values = requirement["resource_property"].split(".")
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
