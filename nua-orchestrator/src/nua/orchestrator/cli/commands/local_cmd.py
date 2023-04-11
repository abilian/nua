"""Nua main scripts."""
from operator import itemgetter

from nua.orchestrator.app_deployment import AppDeployment

from ... import __version__, config


# NOTE: /tmp is not ideal, but /run would require some privileges: see later.
# see later for log module implementation
def status(_cmd: str = ""):
    status_local()
    status_deployed()


def display_configured_registries():
    """Show configured registries."""
    registries = config.read("nua", "registry")
    print("Configured registries:")
    for reg in sorted(registries, key=itemgetter("priority")):
        msg = (
            f'  priority: {reg["priority"]:>2}   '
            f'format: {reg["format"]:<16}   '
            f'url: {reg["url"]}'
        )
        print(msg)


def status_local():
    """Print some status information about local installation."""
    # fixme: go further on status details (sub servers...)
    print(f"Nua version: {__version__}")
    display_configured_registries()


def status_deployed():
    deployer = AppDeployment()
    deployer.load_deployed_configuration()
    deployer.display_deployment_status()


def reload_servers():
    """Rebuild config and restart apps."""
    pass
