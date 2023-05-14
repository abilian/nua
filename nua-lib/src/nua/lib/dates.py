from datetime import datetime, timezone


def backup_date() -> str:
    """Return a string og the current datetime for backup files."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%0H%0M%0S")
