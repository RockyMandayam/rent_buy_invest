import datetime

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.config import Config
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.configs.rent_config import RentConfig


class ExperimentConfig(Config):
    """Stores experiment config.

    Class Attributes:
        schema_path (str): Experiment config schema path

    Instance Attributes:
        mode (str): Which comparison to run; one of MODES
        num_years (int): Number of years to run the projection for
        market_config (MarketConfig): MarketConfig
        rent_config (RentConfig | None): RentConfig; None in RENTAL_VS_INVEST
            mode, which has no rent side.
        buy_config (BuyConfig): BuyConfig
        personal_config (PersonalConfig): PersonalConfig
        start_date: (datetime.datetime): Start date of the projection
    """

    # Renting a home to live in vs buying one to live in.
    RENT_VS_BUY = "rent_vs_buy"
    # Buying a property to rent out vs putting the same money in the market.
    # Where you live is identical either way, so it cancels and does not appear.
    RENTAL_VS_INVEST = "rental_vs_invest"
    MODES = (RENT_VS_BUY, RENTAL_VS_INVEST)

    MAX_NUM_YEARS = 300

    @classmethod
    def schema_path(cls) -> str:
        return "rent_buy_invest/configs/schemas/experiment-config-schema.json"

    def __init__(
        self,
        mode: str,
        num_years: int,
        market_config_path: str,
        rent_config_path: str | None,
        buy_config_path: str,
        personal_config_path: str,
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
        self.mode: str = mode
        self.num_years: int = num_years
        self.market_config: MarketConfig = MarketConfig.parse(market_config_path)
        # None in RENTAL_VS_INVEST mode; nothing on that path reads it
        self.rent_config: RentConfig | None = (
            RentConfig.parse(rent_config_path) if rent_config_path else None
        )
        self.buy_config: BuyConfig = BuyConfig.parse(buy_config_path)
        self.personal_config: PersonalConfig = PersonalConfig.parse(
            personal_config_path
        )
        self.start_date: datetime.datetime = start_date
        self._validate()

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any experiment configs are invalid
        """
        assert (
            self.mode in ExperimentConfig.MODES
        ), f"mode must be one of {ExperimentConfig.MODES}; received {self.mode}"
        # The mode decides which configs are needed. Renting only enters the
        # rent-vs-buy comparison; the other mode has no rent side at all, so a rent
        # config there would be a file that changes nothing.
        if self.mode == ExperimentConfig.RENT_VS_BUY:
            assert (
                self.rent_config is not None
            ), "rent_config_path is required when mode is 'rent_vs_buy'."
        else:
            assert self.rent_config is None, (
                "rent_config_path must be null when mode is 'rental_vs_invest'; "
                "that comparison has no rent side, so the config would be unused."
            )
            assert self.buy_config.rental_income_config is not None, (
                "mode 'rental_vs_invest' needs a buy_config with a "
                "rental_income_config; one without describes a home that is lived "
                "in, which earns no rent and is not depreciated."
            )
        assert (
            self.num_years > 0 and self.num_years <= ExperimentConfig.MAX_NUM_YEARS
        ), f"Number of months must be positive and at most {ExperimentConfig.MAX_NUM_YEARS}."
        assert isinstance(
            self.start_date, datetime.date
        ), f"Must pass in valid start date in 'YYYY-MM-DD' format with no time (only date); received {self.start_date}"
