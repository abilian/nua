BACKUP_RESTORE_FCT = {"pg_dumpall": "pg_psql"}


def restore_fct_id(backup_id: str) -> str:
    return BACKUP_RESTORE_FCT.get(backup_id, "")
