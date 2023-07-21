from abc import ABC

from ..utils import io_utils


class Config(ABC):
    """Abstract config class.

    Note that although this is an abstract class, python does not prevent it
    from being instantiated. Please do not instantiate this class.
    """

    @classmethod
    def parse(cls, filename: str) -> "Config":
        return cls(**io_utils.load_yaml(filename))
