import yaml

from typing import Dict, Any

from ..utils import math_utils


class RentConfig():
    """Stores rent config.

    TODO: maybe I don't need this documentation
    Documentation of the instance variable types:
        self.monthly_rent (float): Monthly rent for first month
        self.monthly_utilities (float): Monthly utilities for the first month
        self.monthly_renters_insurance (float): Monthly renters insurance for
            the first month
        self.monthly_parking_fee (float): Monthly parking fee
        self.annual_rent_inflation_rate (float): ANNUAL rent inflation rate.
            This will be applied to all rent-related expenses.E.g., not just
            rent but also utilities, etc.
        self.inflation_adjustment_period (int): How often (in months) to update
            rent-related expenses for inflation. If you rent with 12-month
            leases, 12 is a good number here.
    """

    def __init__(
        self,
        **kwargs: Dict[str, Any] # too many to type
    ) -> None:
        """Initializes the class.

        To see why I don't use yaml tags, see the docstring for __init__
        in GeneralConfig.
        """
        self.monthly_rent: float = kwargs["monthly_rent"]
        self.monthly_utilities: float = kwargs["monthly_utilities"]
        self.monthly_renters_insurance: float = kwargs["monthly_renters_insurance"]
        self.monthly_parking_fee: float = kwargs["monthly_parking_fee"]
        self.annual_rent_inflation_rate: float = kwargs["annual_rent_inflation_rate"]
        self.inflation_adjustment_period: int = kwargs["inflation_adjustment_period"]

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any rent configs are invalid
        """
        assert self.monthly_rent >= 0, "Monthly rent must be non-negative."
        assert self.monthly_utilities >= 0, "Monthly utilities must be non-negative."
        assert (
            self.monthly_renters_insurance >= 0
        ), "Monthly renter's insurance must be non-negative."
        assert (
            self.monthly_parking_fee >= 0
        ), "Monthly parking fee must be non-negative."
        assert (
            self.inflation_adjustment_period >= 1
        ), "Inflation adjustment period must be at least 1."

    @staticmethod
    def parse_rent_config() -> "RentConfig":
        """Load rent config yaml file as an instance of this class

        Raises:
            AssertionError: If any rent configs are invalid
        """
        # TODO replace this absolute path string literal
        with open(
            "/Users/rocky/Downloads/rent_buy_invest/configs/rent-config.yaml"
        ) as f:
            rent_config: Dict[str, Any] = yaml.load(f, Loader=yaml.Loader)
        rent_config = RentConfig(**rent_config)
        rent_config._validate()
        return rent_config

    def _get_total_monthly_cost(self) -> float:
        """Get total monthly cost of renting for the first month"""
        return (
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
            self._get_total_monthly_cost(),
            self.annual_rent_inflation_rate,
            False,
            num_months,
        )


if __name__ == "__main__":
    print("Parsing rent config")
    c = RentConfig.parse_rent_config()
    print(c)
    print("Done parsing rent config")
