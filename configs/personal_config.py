import math
from typing import Any

from rent_buy_invest.configs.config import Config
from rent_buy_invest.utils import math_utils


class PersonalConfig(Config):
    """Stores personal config.

    Class attributes:
        schema_path (str): Rent config schema path

    Instance attributes:
        See rent_buy_invest/configs/schemas/personal-config-schema for documentation
            instance attributes.
    """

    MAX_ORDINARY_INCOME = 100000000
    MAX_ORDINARY_INCOME_GROWTH_RATE = 0.35
    MAX_YEARS_TILL_RETIREMENT = 80

    @classmethod
    def schema_path(cls) -> str:
        return "rent_buy_invest/configs/schemas/personal-config-schema.json"

    def __init__(self, **kwargs: dict[str, Any]) -> None:  # too many to type
        """Initializes the class.

        To see why I don't use yaml tags, see the docstring for __init__
        in Config.
        """
        self.ordinary_income: float = kwargs["ordinary_income"]
        self.ordinary_income_growth_rate: float = kwargs["ordinary_income_growth_rate"]
        self.years_till_retirement: int = kwargs["years_till_retirement"]
        self._validate()

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any personal configs are invalid
        """
        for attribute, value in self.__dict__.items():
            assert math.isfinite(
                value
            ), f"'{attribute}' attribute must not be NaN, infinity, or negative infinity."
        assert self.ordinary_income >= 0, "Ordinary income must be positive."
        # assert ordinary_income_growth_rate >= -1 so that you can't ever lose all your income...
        assert (
            self.ordinary_income_growth_rate >= -1
        ), "Ordinary income growth rate must be at least -1."
        assert (
            self.years_till_retirement >= 0
        ), "years_till_retirement must be non-negative"

        self._validate_max_value("ordinary_income", PersonalConfig.MAX_ORDINARY_INCOME)
        self._validate_max_value(
            "ordinary_income_growth_rate",
            PersonalConfig.MAX_ORDINARY_INCOME_GROWTH_RATE,
        )
        self._validate_max_value(
            "years_till_retirement", PersonalConfig.MAX_YEARS_TILL_RETIREMENT
        )

    def get_ordinary_incomes(self, num_months: int) -> list[float]:
        assert num_months > 0
        first_month_ordinary_income = self.ordinary_income / math_utils.MONTHS_PER_YEAR
        months_till_retirement = self.years_till_retirement * math_utils.MONTHS_PER_YEAR
        if months_till_retirement >= num_months:
            return math_utils.project_growth(
                principal=first_month_ordinary_income,
                annual_growth_rate=self.ordinary_income_growth_rate,
                compound_monthly=False,
                num_months=num_months,
            )
        else:  # retire during projection
            ordinary_incomes_during_growth = math_utils.project_growth(
                principal=first_month_ordinary_income,
                annual_growth_rate=self.ordinary_income_growth_rate,
                compound_monthly=False,
                num_months=months_till_retirement,
            )
            ordinary_incomes_during_retirement = [0] * (
                num_months - months_till_retirement
            )
            return ordinary_incomes_during_growth + ordinary_incomes_during_retirement
