import math
from typing import Any

from rent_buy_invest.configs.config import Config
from rent_buy_invest.utils import math_utils


class RentConfig(Config):
    """Stores rent config.

    Class attributes:
        schema_path (str): Rent config schema path

    Instance attributes:
        See rent_buy_invest/configs/schemas/rent-config-schema for documentation
            instance attributes.
    """

    MAX_MONTHLY_UTILITIES_AS_FRACTION_OF_RENT = 0.5
    MAX_MONTHLY_RENTERS_INSURANCE_AS_FRACTION_OF_RENT = 0.5
    MAX_MONTHLY_PARKING_FEE_AS_FRACTION_OF_RENT = 0.5
    MAX_ANNUAL_RENT_INFLATION_RATE = 1.0
    MAX_SECURITY_DEPOSIT_AS_FRACTION_OF_RENT = 6

    @classmethod
    def schema_path(cls) -> str:
        return "rent_buy_invest/configs/schemas/rent-config-schema.json"

    def __init__(self, **kwargs: dict[str, Any]) -> None:  # too many to type
        """Initializes the class.

        To see why I don't use yaml tags, see the docstring for __init__
        in Config.
        """
        self.monthly_rent: float = kwargs["monthly_rent"]
        self.monthly_utilities: float = kwargs["monthly_utilities"]
        self.monthly_renters_insurance: float = kwargs["monthly_renters_insurance"]
        self.monthly_parking_fee: float = kwargs["monthly_parking_fee"]
        self.annual_rent_inflation_rate: float = kwargs["annual_rent_inflation_rate"]
        self.inflation_adjustment_period: int = kwargs["inflation_adjustment_period"]
        self.security_deposit: float = kwargs["security_deposit"]
        self.unrecoverable_fraction_of_security_deposit: float = kwargs[
            "unrecoverable_fraction_of_security_deposit"
        ]
        self.subsidy_fraction: float = kwargs["subsidy_fraction"]
        self._validate()

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any rent configs are invalid
        """
        for attribute, value in self.__dict__.items():
            assert math.isfinite(
                value
            ), f"'{attribute}' attribute must not be NaN, infinity, or negative infinity."
        assert self.monthly_rent > 0, "Monthly rent must be positive."
        assert self.monthly_utilities >= 0, "Monthly utilities must be non-negative."
        assert (
            self.monthly_renters_insurance >= 0
        ), "Monthly renter's insurance must be non-negative."
        assert (
            self.monthly_parking_fee >= 0
        ), "Monthly parking fee must be non-negative."
        assert (
            self.inflation_adjustment_period >= 1
        ), "Inflation adjustment period must be an integer of at least 1."
        assert self.security_deposit >= 0, "Security deposit must be non-negative."
        assert (
            self.unrecoverable_fraction_of_security_deposit >= 0
            and self.unrecoverable_fraction_of_security_deposit <= 1
        ), "Unrecoverable fraction of security deposit must be between 0 and 1 inclusive."
        assert (
            self.subsidy_fraction >= 0 and self.subsidy_fraction <= 1
        ), "Subsidy fraction of rental costs must be between 0 and 1 inclusive."
        self._validate_max_value_as_fraction(
            "monthly_utilities",
            "monthly_rent",
            RentConfig.MAX_MONTHLY_UTILITIES_AS_FRACTION_OF_RENT,
        )

        self._validate_max_value_as_fraction(
            "monthly_renters_insurance",
            "monthly_rent",
            RentConfig.MAX_MONTHLY_RENTERS_INSURANCE_AS_FRACTION_OF_RENT,
        )
        self._validate_max_value_as_fraction(
            "monthly_parking_fee",
            "monthly_rent",
            RentConfig.MAX_MONTHLY_PARKING_FEE_AS_FRACTION_OF_RENT,
        )
        self._validate_max_value(
            "annual_rent_inflation_rate", RentConfig.MAX_ANNUAL_RENT_INFLATION_RATE
        )
        self._validate_max_value_as_fraction(
            "security_deposit",
            "monthly_rent",
            RentConfig.MAX_SECURITY_DEPOSIT_AS_FRACTION_OF_RENT,
        )

    def get_upfront_one_time_cost(self) -> float:
        return (
            (1 - self.subsidy_fraction)
            * self.security_deposit
            * self.unrecoverable_fraction_of_security_deposit
        )

    def _get_first_monthly_cost(self) -> float:
        """Get monthly cost of renting for the first month"""
        return (1 - self.subsidy_fraction) * (
            self.monthly_rent
            + self.monthly_utilities
            + self.monthly_renters_insurance
            + self.monthly_parking_fee
        )

    def get_monthly_costs_of_renting(self, num_months: int) -> float:
        """Return the monthly cost of renting each month for num_months months.

        Returns:
            List[float]: monthly cost of renting in dollars rounded to two
                decimal points.

        Raises:
            AssertionError: If num_months is not positive
        """
        return math_utils.project_growth(
            self._get_first_monthly_cost(),
            self.annual_rent_inflation_rate,
            False,
            num_months,
        )
