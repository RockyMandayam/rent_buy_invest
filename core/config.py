from abc import ABC, abstractmethod

from rent_buy_invest.utils import io_utils


class Config(ABC):
    """Abstract config class.

    Note that although this is an abstract class, python does not prevent it
    from being instantiated. Please do not instantiate this class.
    """

    @abstractmethod
    def __init__(self):
        pass

    @classmethod
    def parse(cls, project_path: str) -> "Config":
        """Returns object with type equal to the calling class using arguments
        provided in the yaml file with the given path.

        Args:
            project_path (str): Path (from top-level directory) to yaml file

        Returns:
            cls: Object with type equal to the calling class (whicch will be a
                descendent of this class)
        """
        return cls(**io_utils.read_yaml(project_path))
