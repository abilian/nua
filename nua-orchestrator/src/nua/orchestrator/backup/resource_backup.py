from __future__ import annotations

import typing

from .backup_registry import get_backup_plugin
from .backup_report import BackupReport

if typing.TYPE_CHECKING:
    from ..resource import Resource


def backup_resource(resource: Resource) -> BackupReport:
    """Execute a backup from main 'backup' configuration of a Resource."""
    config = resource.backup
    report = BackupReport(node=resource.container_name)
    if not config or not isinstance(config, dict):
        report.task = False
        report.success = False
        report.message = "No backup configuration"
        return report
    backup_class = get_backup_plugin(config.get("method", ""))
    if backup_class is None:
        report.task = True
        report.success = False
        report.message = f"Unknown backup method '{backup_class}'"
        return report
    backup = backup_class(resource)
    report = backup.run()
    return report
