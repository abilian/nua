from __future__ import annotations

import typing

from .backup_registry import get_backup_plugin
from .backup_report import BackupReport

if typing.TYPE_CHECKING:
    from ..provider import Provider


def backup_provider(
    provider: Provider,
    ref_date: str = "",
) -> list[BackupReport]:
    """Execute a backup from main 'backup' configuration of a Provider."""
    config = provider.backup
    # debug backup print(config)
    report = BackupReport(node=provider.container_name)
    if not config or not isinstance(config, dict):
        report.task = False
        report.success = False
        report.message = "No backup configuration"
        return [report]
    method = config.get("method") or ""
    backup_class = get_backup_plugin(method)
    if backup_class is None:
        report.task = True
        report.success = False
        report.message = f"Unknown backup method '{method}'"
        return [report]
    backup = backup_class(provider, ref_date=ref_date)
    reports = backup.run_on_provider()
    return reports
