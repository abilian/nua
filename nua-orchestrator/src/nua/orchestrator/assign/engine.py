"""Functions to respond to requirement from instance declarations."""
from collections.abc import Callable
from pprint import pformat

from nua.lib.panic import info, show, warning
from nua.lib.tool.state import verbosity

from ..app_instance import AppInstance
from ..persistent import Persistent
from ..resource import Resource
from ..utils import dehyphen
from .evaluators import (  # site_environment,
    external_ip_evaluation,
    nua_internal,
    random,
    resource_property,
    unique_db,
    unique_user,
)

EVALUATOR_FCT = {
    "key": resource_property,
    # "environment": site_environment,
    "nua_internal": nua_internal,
    "external_ip": external_ip_evaluation,
    "random": random,
    # "property": resource_property,
    "unique_db": unique_db,
    "unique_user": unique_user,
}
EVALUATOR_LATE_FCT = {}


def instance_key_evaluator(
    site: AppInstance,
    resource: Resource | None = None,
    late_evaluation: bool = False,
    port: dict | None = None,
) -> dict:
    """Evaluate value for 'env' values declared as dict with dynamic
    parameters, through retrieving persistent value or compute value from
    specialized functions."""
    result = {}
    if resource is None:
        resource = site
        persistent = site.persistent("")
    else:
        persistent = site.persistent(resource.resource_name)
    if port is None:
        dynamics = {k: v for k, v in resource.env.items() if isinstance(v, dict)}
    else:
        dynamics = {k: v for k, v in port.items() if isinstance(v, dict)}
    with verbosity(3):
        info(f"instance_key_evaluator ({late_evaluation=}):\n    {pformat(dynamics)}")
    if not dynamics:
        return {}
    for destination_key, requirement in dynamics.items():
        evaluate_requirement(
            resource,
            destination_key,
            requirement,
            persistent,
            result,
            late_evaluation,
        )
    site.set_persistent(persistent)
    return result


def evaluate_requirement(
    resource: Resource,
    destination_key: str,
    requirement: dict,
    persistent: Persistent,
    env: dict,
    late_evaluation: bool,
) -> None:
    function = required_function(
        requirement,
        late_evaluation,
    )
    if function:
        result = function(
            resource,
            destination_key,
            requirement,
            persistent,
        )
        with verbosity(3):
            show(f"generated value: {result}")
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
