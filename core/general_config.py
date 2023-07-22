from typing import Any, Dict

import yaml

from rent_buy_invest.core.config import Config
from rent_buy_invest.utils import io_utils


class GeneralConfig(Config):
    # TODO test this class
    """Stores general config.

    Documentation of the instance variable types:
    # TODO add documentation
    # TODO maybe just point to the yaml file
    """

    def __init__(self, num_months: int) -> None:
        """Initializes the class.

        To easily convert a yaml file to a class, there is the option of using
        a yaml tag. To use this, you simply set a class variable yaml_tag =
        "!GeneralConfig" and in the yaml file use "--- !GeneralConfig" at the
        top of the file to indicate that you are specifying a GeneralConfig
        object. However, this makes it hard to use jsonschema for validation.
        Also, this approach does not require defining the __init__ method,
        which is awkward. First, it prevents doing some sanity/validation
        checks in __init__. Second, it means that there is still a default
        empty __init__ so invalid GeneralConfig objects can still be created.
        Of course, I can implement __init__ to just raise an Exception, but
        this approach seems bad.
        """
        self.num_months: int = num_months
        self._validate()

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any general configs are invalid
        """
        # make 150 if parameter and maybe appropriately update the yaml comment
        assert (
            self.num_months > 0 and self.num_months <= 150
        ), "Number of months must be positive and at most 150."
