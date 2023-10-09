from operator import itemgetter
from typing import Any

from nua.orchestrator import __version__, config
from nua.orchestrator.app_deployer import AppDeployer
from nua.orchestrator.state_journal import StateJournal


class StatusCommand:
    """Status of orchestrator."""

    def __init__(self):
        self._registries: list[dict] = []
        self._deploy_status: dict[str, Any] = {}

    def display(self) -> None:
        """Directly print the current orchestrator status for CLI."""
        print(f"Nua version: {__version__}\n")
        print(self._configured_registries())
        print()
        state = StateJournal()
        state.read_current_state()
        deployer = AppDeployer()
        deployer.load_deployed_state(state.deployed_state())
        deployer.display_deployment_status()

    def read(self) -> None:
        """Read Orchestrator registries and deployment statuses."""
        self._read_registries()
        self._read_deployed()

    def _read_registries(self) -> None:
        """Read Orchestrator registries configuration."""
        self._registries = config.read("nua", "registry") or []  # type: ignore

    def _read_deployed(self) -> None:
        """Read Orchestrator deployed apps status."""
        state = StateJournal()
        state.read_current_state()
        deployer = AppDeployer()
        deployer.load_deployed_state(state.deployed_state())
        self._deploy_status = deployer.deployment_status_records()

    def as_dict(self) -> dict[str, Any]:
        """Return orichestrator status as a dict."""
        result: dict[str, Any] = {"version": __version__}
        result["registries"] = self._registries
        result.update(self._deploy_status)
        return result

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
