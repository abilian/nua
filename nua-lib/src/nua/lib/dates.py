from datetime import datetime, timezone


def backup_date() -> str:
    """Return a string of the current datetime for backup files.

    Format: 2023-05-30-120255
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%0H%0M%0S")
