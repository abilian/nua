"""Functions to respond to requirement from instance declarations."""
from collections.abc import Callable

from nua.lib.panic import info, warning
from nua.lib.tool.state import verbosity

# from . import config
from .evaluators import random_str, resource_property
from .site import Site

EVALUATOR_FCT = {
    "random_str": random_str,
    "resource_property": resource_property,
}


def instance_key_evaluator(site: Site) -> dict:
    env = {}
    for requirement in site.instance_key_requirements():
        destination_key = requirement["key"]
        function = required_function(requirement)
        if function:
            env[destination_key] = function(site, requirement)
            if verbosity(2):
                info(
                    f"generated value for '{destination_key}': '{env[destination_key]}'"
                )
        else:
            warning(
                f"Requirement maybe not valid for {destination_key}, key set to empty"
            )
            env[destination_key] = ""
    return env


def required_function(requirement: dict) -> Callable | None:
    for name, function in EVALUATOR_FCT.items():
        if name in requirement:
            return function
    return None
