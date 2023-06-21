from operator import itemgetter
from typing import Any

from nua.orchestrator import __version__, config
from nua.orchestrator.app_deployment import AppDeployment


class StatusCommand:
    """Status of orchestrator."""

    def __init__(self):
        self._registries: list[dict] = []

    def display(self) -> None:
        """Show current orichestrator status as a string."""
        print(f"Nua version: {__version__}\n")
        print(self._configured_registries())
        print()
        deployer = AppDeployment()
        deployer.load_deployed_configuration()
        deployer.display_deployment_status()

    def as_dict(self) -> dict[str, Any]:
        """Return current orichestrator status as a dict."""
        self._read_registries()
        result: dict[str, Any] = {"version": __version__}
        result["registries"] = self._registries
        deployer = AppDeployment()
        deployer.load_deployed_configuration()
        result.update(deployer.deployment_status_records())
        return result

    def _read_registries(self):
        """Read Orchestrator registries configuration."""
        self._registries = config.read("nua", "registry") or []  # type: ignore

    def _configured_registries(self) -> str:
        """Return configured registries as string."""
        lines: list[str] = []
        self._read_registries()
        lines.append("Configured registries:")
        for reg in sorted(self._registries, key=itemgetter("priority")):
            lines.append(
                (
                    f'  priority: {reg["priority"]:>2}   '
                    f'format: {reg["format"]:<16}   '
                    f'url: {reg["url"]}'
                )
            )
        return "\n".join(lines)
