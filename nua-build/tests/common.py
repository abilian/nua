from pathlib import Path


def get_apps_root_dir(subdir: str = None) -> Path:
    """Return the path to the root of the apps directory."""
    path = Path(__file__).parent.parent.parent / "apps"
    if subdir is None:
        return path
    else:
        return path / subdir
