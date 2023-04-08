from dataclasses import dataclass


@dataclass
class BackupReport:
    node: str = ""
    task: bool = False
    success: bool = True
    message: str = ""


def global_backup_report(reports: list[BackupReport]) -> str:
    if not reports:
        return ""

    main_site = reports[-1]
    main_name = main_site.node

    if any(rep.task for rep in reports):
        if all(rep.success for rep in reports if rep.task):
            result = f"Backup tasks successful for {main_name}"
        else:
            result = _failed_backup_report(reports)
    else:
        result = f"No backup task for {main_name}"

    return result


def _failed_backup_report(reports: list[BackupReport]) -> str:
    result = ["Some backup task did fail:"]
    success_str = {True: "succeed", False: "failed"}
    for rep in reports:
        if not rep.task:
            continue
        result.append(f"  {rep.node}, {success_str[rep.success]}: {rep.message}")
    return "\n".join(result)
