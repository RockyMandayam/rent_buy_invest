import datetime

from rent_buy_invest.core.config import Config
from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.core.market_config import MarketConfig
from rent_buy_invest.core.rent_config import RentConfig


class ExperimentConfig(Config):
    """Stores experiment config.

    Class Attributes:
        schema_path (str): Experiment config schema path

    Instance Attributes:
        num_months (int): Number of months to run the projection for
        market_config (MarketConfig): MarketConfig
        rent_config (RentConfig): RentConfig.
        house_config: (HouseConfig): HouseConfig
        start_date: (datetime.datetime): Start date of the projection
    """

    MAX_NUM_MONTHS = 3600

    @classmethod
    @property
    def schema_path(cls) -> str:
        return "rent_buy_invest/configs/schemas/experiment-config-schema.json"

    def __init__(
        self,
        num_months: int,
        market_config_path: str,
        rent_config_path: str,
        house_config_path: str,
        start_date: datetime.datetime,
    ) -> None:
        """Initializes the class.

        To easily convert a yaml file to a class, there is the option of using
        a yaml tag. To use this, you simply set a class variable yaml_tag =
        "!ExperimentConfig" and in the yaml file use "--- !ExperimentConfig" at
        the top of the file to indicate that you are specifying a
        ExperimentConfig object. However, this makes it hard to use jsonschema
        for validation. Also, this approach does not require defining the
        __init__ method, which is awkward. First, it prevents doing some
        sanity/validation checks in __init__. Second, it means that there is
        still a default empty __init__ so invalid ExperimentConfig objects can
        still be created. Of course, I can implement __init__ to just raise an
        Exception, but this approach seems bad.
        """
        assert num_months <= ExperimentConfig.MAX_NUM_MONTHS
        self.num_months: int = num_months
        self.market_config: MarketConfig = MarketConfig.parse(market_config_path)
        self.rent_config: RentConfig = RentConfig.parse(rent_config_path)
        self.house_config: HouseConfig = HouseConfig.parse(house_config_path)
        self.start_date: datetime.datetime = start_date
        self._validate()

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any experiment configs are invalid
        """
        # make 150 if parameter and maybe appropriately update the yaml comment
        assert (
            self.num_months > 0 and self.num_months <= 2400
        ), "Number of months must be positive and at most 2400."
        assert isinstance(
            self.start_date, datetime.date
        ), "Must pass in valid start date in 'YYYY-MM-DD' format with no time (only date)."
