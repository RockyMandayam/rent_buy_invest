from abc import ABC

from rent_buy_invest.utils import io_utils, path_utils


class Config(ABC):
    """Abstract config class.

    Note that although this is an abstract class, python does not prevent it
    from being instantiated. Please do not instantiate this class.
    """

    @classmethod
    def parse(cls, project_path: str) -> "Config":
        return cls(**io_utils.load_yaml(path_utils.get_abs_path(project_path)))
