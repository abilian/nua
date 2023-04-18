"""Base class for detect and install project."""
import abc


class BaseDetector(abc.ABC):
    """Base class for detect and install project."""

    message = ""

    @classmethod
    def info(cls) -> str:
        return cls.message

    @classmethod
    def detect(cls) -> bool:
        return False

    @classmethod
    def install(cls) -> None:
        pass
