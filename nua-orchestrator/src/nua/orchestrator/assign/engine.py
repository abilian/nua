"""Functions to respond to requirement from instance declarations."""
from collections.abc import Callable
from pprint import pformat

from nua.lib.panic import info, warning
from nua.lib.tool.state import verbosity

from ..resource import Resource
from ..site import Site
from ..utils import dehyphen

# from . import config
from .evaluators import (
    nua_internal,
    random_str,
    resource_property,
    site_environment,
    unique_db,
    unique_user,
)

EVALUATOR_FCT = {
    "environment": site_environment,
    "nua_internal": nua_internal,
    "random_str": random_str,
    "resource_property": resource_property,
    "unique_db": unique_db,
    "unique_user": unique_user,
}
EVALUATOR_LATE_FCT = {}


def instance_key_evaluator(
    site: Site, resource: Resource | None = None, late_evaluation: bool = False
) -> dict:
    """Evaluate value for an 'assign' key, through retrieving persistent value or
    compute value from 'assign' defined function.
    """
    env = {}
    if resource is None:
        resource = site
        persistent = site.persistent("")
    else:
        persistent = site.persistent(resource.resource_name)
    if verbosity(3):
        info(f"resource.assign ({late_evaluation=}):\n    {pformat(resource.assign)}")
    for requirement in resource.assign:
        destination_key = requirement["key"]
        function = required_function(requirement, late_evaluation)
        if function:
            result = function(resource, requirement, persistent)
            if verbosity(2):
                info(f"generated value: {result}")
        else:
            warning(
                f"Requirement maybe not valid for {destination_key}, key set to empty"
            )
            result = {destination_key: ""}
        env.update(result)
    site.set_persistent(persistent)
    return env


def required_function(requirement: dict, late: bool = False) -> Callable | None:
    if late:
        evaluator_fct = EVALUATOR_LATE_FCT
    else:
        evaluator_fct = EVALUATOR_FCT
    for name, function in evaluator_fct.items():
        if dehyphen(name) in requirement:
            return function
    return None