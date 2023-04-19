"""Base class for detect and install project."""
import abc


class BaseDetector(abc.ABC):
    """Base class for detect and install project.

    BaseDetector.priority: permits to sort the tests order (lower value is higher
    priority) of each detector upon a source directory. Thus testing dual
    installation (ie: python+node) before single ones."""

    message: str = ""
    priority: int = 100

    @classmethod
    def info(cls) -> str:
        return cls.message

    @classmethod
    def detect(cls) -> bool:
        return False

    @classmethod
    def install(cls) -> None:
        pass
