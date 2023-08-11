from abc import ABC, abstractmethod
import jsonschema

from rent_buy_invest.utils import io_utils

class Config(ABC):
    """Abstract config class."""

    @abstractmethod
    def __init__(self):
        pass

    @classmethod
    @property
    @abstractmethod
    def schema_path(cls) -> str:
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
        config_schema = io_utils.read_json(cls.schema_path)
        config_kwargs = io_utils.read_yaml(project_path)
        jsonschema.validate(instance=config_kwargs, schema=config_schema)
        return cls(**config_kwargs)
