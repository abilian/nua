from __future__ import annotations

import typing

from .backup_registry import get_backup_plugin
from .backup_report import BackupReport

if typing.TYPE_CHECKING:
    from ..resource import Resource
    from ..volume import Volume


def backup_volume(resource: Resource, volume: Volume) -> BackupReport:
    """Execute a backup from backup tag of a Volume of a Resource."""
    config = volume.backup
    report = BackupReport(node=volume.full_name)
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
    backup = backup_class(resource, volume)
    return backup.run()
