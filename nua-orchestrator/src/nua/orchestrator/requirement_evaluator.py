"""Functions to respond to requirement from instance declarations."""
from collections.abc import Callable

from nua.lib.panic import info, warning
from nua.lib.tool.state import verbosity

# from . import config
from .evaluators import nua_internal, random_str, resource_property
from .site import Site

EVALUATOR_FCT = {
    "random_str": random_str,
    "resource_property": resource_property,
    "nua_internal": nua_internal,
}


def instance_key_evaluator(site: Site) -> dict:
    env = {}
    for requirement in site.instance_key_requirements():
        destination_key = requirement["key"]
        function = required_function(requirement)
        if function:
            result = function(site, requirement)
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
