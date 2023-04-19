"""Base class for detect and install project."""
import abc

from nua.lib.actions import install_build_packages, installed_packages


class BaseDetector(abc.ABC):
    """Base class for detect and install project.

    BaseDetector.priority: permits to sort the tests order (lower value is higher
    priority) of each detector upon a source directory. Thus testing dual
    installation (ie: python+node) before single ones."""

    message: str = ""
    priority: int = 100
    build_packages: list[str] = []
    run_packages: list[str] = []  # currently not implemented

    @classmethod
    def info(cls) -> str:
        return cls.message

    @classmethod
    def detect(cls) -> bool:
        return False

    @classmethod
    def install_with_build_packages(cls) -> None:
        if cls.build_packages:
            with install_build_packages(
                cls.build_packages,
                installed=installed_packages(),
                keep_lists=True,
            ):
                cls.install()
        else:
            cls.install()

    @classmethod
    def install(cls) -> None:
        pass
