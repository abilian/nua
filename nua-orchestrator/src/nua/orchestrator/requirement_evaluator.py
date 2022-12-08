"""Functions to respond to requirement from instance declarations."""
from collections.abc import Callable

from nua.lib.panic import info, warning
from nua.lib.tool.state import verbosity

# from . import config
from .evaluators import nua_internal, random_str, resource_property
from .resource import Resource
from .site import Site

EVALUATOR_FCT = {
    "random_str": random_str,
    "resource_property": resource_property,
    "nua_internal": nua_internal,
}


def instance_key_evaluator(resource: Resource) -> dict:
    env = {}
    if verbosity(3):
        info(f"resource.assign: {resource.assign}")
    for requirement in resource.assign:
        destination_key = requirement["key"]
        function = required_function(requirement)
        if function:
            result = function(resource, requirement)
            if verbosity(2):
                info(f"generated value: {result}")
        else:
            warning(
                f"Requirement maybe not valid for {destination_key}, key set to empty"
            )
            result = {destination_key: ""}
        env.update(result)
    return env


def required_function(requirement: dict) -> Callable | None:
    for name, function in EVALUATOR_FCT.items():
        if name in requirement:
            return function
    return None
