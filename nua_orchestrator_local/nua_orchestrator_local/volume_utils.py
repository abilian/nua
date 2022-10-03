"""Volumes management.

At the moment, concepts may be close to Docker volumes/binds.
"""


def filter_empty_dicts(input: list) -> list:
    return [x for x in input if x]


def volumes_merge_config(site: dict) -> list:
    """Return the list of volumes declared for the site.

    Taking into account both the volumes declared in the base configuration of the
    image and the possible modification from the instance configuration.
    """
    image_volumes = filter_empty_dicts(site["image_nua_config"].get("volume") or [])
    instance_volumes = filter_empty_dicts(site.get("volume") or [])
    if not instance_volumes:
        return image_volumes
    volumes_dict = {}
    for vol in image_volumes + instance_volumes:
        volumes_dict["source"] = vol
    return list(volumes_dict.values())
