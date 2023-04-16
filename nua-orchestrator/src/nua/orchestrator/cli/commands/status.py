from operator import itemgetter

from nua.orchestrator import __version__, config
from nua.orchestrator.app_deployment import AppDeployment

# NOTE: /tmp is not ideal, but /run would require some privileges: see later.
# see later for log module implementation


class StatusCommand:
    """Status of orchestrator."""

    def __call__(self, _cmd: str = ""):
        self._status_local()
        self._status_deployed()

    def _status_local(self):
        """Print some status information about local installation."""
        # fixme: go further on status details (sub servers...)
        print(f"Nua version: {__version__}")
        print()
        self._display_configured_registries()
        print()

    def _status_deployed(self):
        deployer = AppDeployment()
        deployer.load_deployed_configuration()
        deployer.display_deployment_status()

    def _display_configured_registries(self):
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


status = StatusCommand()


def reload_servers():
    """Rebuild config and restart apps."""
    pass
