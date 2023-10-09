from __future__ import annotations

import typing

from .backup_registry import get_backup_plugin
from .backup_report import BackupReport

if typing.TYPE_CHECKING:
    from ..provider import Provider
    from ..volume import Volume


def backup_volume(
    provider: Provider,
    volume: Volume,
    ref_date: str = "",
) -> BackupReport:
    """Execute a backup from backup tag of a Volume of a Provider."""
    config = volume.backup
    report = BackupReport(node=volume.full_name)
    if not config or not isinstance(config, dict):
        report.task = False
        report.success = False
        report.message = "No backup configuration"
        return report
    method = config.get("method") or ""
    backup_class = get_backup_plugin(method)
    if backup_class is None:
        report.task = True
        report.success = False
        report.message = f"Unknown backup method '{method}'"
        return report
    backup = backup_class(provider, volume, ref_date=ref_date)
    report = backup.run()
    return report
