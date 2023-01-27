"""Generate the long nua tag of packages."""


def nua_tag_string(metadata: dict) -> str:
    if release := metadata.get("release", ""):
        suffix = f"-{release}"
    else:
        suffix = ""
    if metadata["id"].startswith("nua-"):
        prefix = ""
    else:
        prefix = "nua-"
    return f"{prefix}{metadata['id']}-{metadata['version']}{suffix}"
