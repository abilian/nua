"""Functions to respond to requirement from instance declarations."""
from collections.abc import Callable
from pprint import pformat

from nua.lib.panic import info, show, warning
from nua.lib.tool.state import verbosity

from ..app_instance import AppInstance
from ..persistent import Persistent
from ..resource import Resource
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
    "property": resource_property,
    "unique_db": unique_db,
    "unique_user": unique_user,
}
EVALUATOR_LATE_FCT = {}


def instance_key_evaluator(
    site: AppInstance,
    resource: Resource | None = None,
    late_evaluation: bool = False,
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
    with verbosity(3):
        info(f"resource.assign ({late_evaluation=}):\n    {pformat(resource.assign)}")
    for requirement in resource.assign:
        evaluate_requirement(resource, requirement, persistent, env, late_evaluation)
    site.set_persistent(persistent)
    return env


def evaluate_requirement(
    resource: Resource,
    requirement: dict,
    persistent: Persistent,
    env: dict,
    late_evaluation: bool,
) -> None:
    destination_key = requirement["key"]
    function = required_function(requirement, late_evaluation)
    if function:
        result = function(resource, requirement, persistent)
        with verbosity(3):
            info(f"generated value: {result}")
    else:
        warning(f"Requirement maybe not valid for {destination_key}, key set to empty")
        result = {destination_key: ""}
    env.update(result)
    maybe_display_value(requirement, result)


def maybe_display_value(requirement: dict, result: dict):
    if requirement.get("display", False):
        for key, val in result.items():
            show(f"Assigned value: '{key}' = '{val}'")


def required_function(requirement: dict, late: bool = False) -> Callable | None:
    if late:
        evaluator_fct = EVALUATOR_LATE_FCT
    else:
        evaluator_fct = EVALUATOR_FCT
    for name, function in evaluator_fct.items():
        if dehyphen(name) in requirement:
            return function
    return None
