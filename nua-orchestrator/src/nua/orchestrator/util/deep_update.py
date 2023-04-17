from collections.abc import Mapping


def deep_update(base: dict, updates: Mapping, depth: int = 2**10):
    for key, val in updates.items():
        if (
            key in base
            and isinstance(base[key], Mapping)
            and isinstance(val, Mapping)
            and depth > 0
        ):
            deep_update(base[key], val, depth - 1)
        else:
            base[key] = val
