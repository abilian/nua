"""Generate the long nua tag of packages.

For container and network names, the ":" will be replaced by "-".
"""


def nua_tag_string(metadata: dict) -> str:
    """Return long tag string with version and release.

    "hedgedoc" -> "nua-hedgedoc:1.9.7-3"
    """
    if release := metadata.get("release", ""):
        suffix = f"-{release}"
    else:
        suffix = ""
    if metadata["id"].startswith("nua-"):
        prefix = ""
    else:
        prefix = "nua-"
    return f"{prefix}{metadata['id']}:{metadata['version']}{suffix}"
