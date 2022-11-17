import pkg_resources


def is_package_installed(pkg_name: str) -> bool:
    """Utility to check if some package is installed."""
    return pkg_name in {pkg.key for pkg in pkg_resources.working_set}
