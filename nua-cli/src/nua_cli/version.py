import importlib.metadata


def get_version() -> str:
    try:
        return importlib.metadata.version("nua.cli")
    except importlib.metadata.PackageNotFoundError:
        return importlib.metadata.version("nua")
