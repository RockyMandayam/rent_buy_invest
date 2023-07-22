from abc import ABC

from rent_buy_invest.utils import io_utils, path_utils


class Config(ABC):
    """Abstract config class.

    Note that although this is an abstract class, python does not prevent it
    from being instantiated. Please do not instantiate this class.
    """

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
        abs_path = path_utils.get_abs_path(project_path)
        return cls(**io_utils.load_yaml(abs_path))
