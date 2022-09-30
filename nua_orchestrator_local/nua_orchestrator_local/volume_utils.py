"""Volumes management.

At the moment, concepts may be close to Docker volumes/binds.
"""


def volumes_merge_config(site: dict) -> list:
    image_volumes = site["image_nua_config"].get("volume") or []
    instance_volumes = site.get("volume") or []
    if not instance_volumes:
        return image_volumes
    volumes_dict = {}
    for vol in image_volumes + instance_volumes:
        volumes_dict["source"] = vol
    return list(volumes_dict.values())
